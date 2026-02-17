"""
This module handles the routes for uploading identity documents related to reservations.
It processes image files, validates them using OCR, and links the uploaded files with
the corresponding client and reservation in the database.

Functions:
- upload_file: Handles the upload of the front and back identity document images and selfies.
"""


#pylint: disable=C0301,E0401,R0914,W0718,W0612,E0611,R0912,R0915,R1702,R0911
import os
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import BadRequest
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from utils.file_utils import allowed_file, sanitize_filename, save_file
from utils.ocr_utils import validate_document
from utils.db_utils import get_reservation_by_id, get_client_by_cf, add_or_update_client, link_client_to_reservation
from utils.email_utils import get_admin_email_config
from email_handler import EmailService
from routes.email_config_routes import get_encryption_key
from app_logging.config import get_logger
from app_logging.decorators import log_route, log_database_operation, log_performance
from app_logging.utils import safe_extra_fields, log_notification_error
from extensions import limiter

upload_bp = Blueprint('upload', __name__, url_prefix="/api/v1")

# Configure logging
logger = get_logger(__name__)
UPLOAD_FOLDER = 'uploads/'
UPLOAD_TOKEN_SALT = "reservation-upload"
UPLOAD_TOKEN_MAX_AGE_SECONDS = 60 * 60 * 2
DOCUMENT_VALIDATION_TOKEN_SALT = "reservation-document-validation"
DOCUMENT_VALIDATION_TOKEN_MAX_AGE_SECONDS = 60 * 15
MAX_UPLOAD_FILE_SIZE_BYTES = int(os.getenv("MAX_UPLOAD_FILE_SIZE_BYTES", 5 * 1024 * 1024))
ALLOWED_UPLOAD_MIME_TYPES = {"image/jpeg", "image/png"}


def _get_uploaded_file_size(uploaded_file):
    """Return uploaded file size in bytes without consuming the stream."""
    stream = getattr(uploaded_file, "stream", None)
    if stream is None:
        return 0

    current_position = stream.tell()
    stream.seek(0, os.SEEK_END)
    size_bytes = stream.tell()
    stream.seek(current_position, os.SEEK_SET)
    return size_bytes


def _validate_upload_file(uploaded_file, field_name):
    """Validate extension, MIME type and size for an uploaded image file."""
    if not uploaded_file or not allowed_file(uploaded_file.filename):
        return f"Invalid file type for {field_name}"

    mime_type = (uploaded_file.mimetype or "").lower().strip()
    if mime_type not in ALLOWED_UPLOAD_MIME_TYPES:
        return f"Invalid MIME type for {field_name}"

    if _get_uploaded_file_size(uploaded_file) > MAX_UPLOAD_FILE_SIZE_BYTES:
        return f"File too large for {field_name}"

    return None


def _build_serializer():
    return URLSafeTimedSerializer(current_app.config["JWT_SECRET_KEY"])


def _parse_upload_token(serializer, upload_token):
    if not upload_token:
        return None, (jsonify({"error": "Missing upload token"}), 401)
    try:
        payload = serializer.loads(
            upload_token,
            salt=UPLOAD_TOKEN_SALT,
            max_age=UPLOAD_TOKEN_MAX_AGE_SECONDS
        )
        return payload, None
    except SignatureExpired:
        return None, (jsonify({"error": "Upload token expired"}), 401)
    except BadSignature:
        return None, (jsonify({"error": "Invalid upload token"}), 401)


def _validate_documents_payload(reservation_id, files_payload):
    reservation_folder = os.path.join(UPLOAD_FOLDER, reservation_id, "validation_tmp")
    os.makedirs(reservation_folder, exist_ok=True)
    validation_results = {}
    invalid_files = []

    try:
        for key in ['frontimage', 'backimage']:
            file = files_payload[key]
            file_error = _validate_upload_file(file, key)
            if file_error:
                raise BadRequest(file_error)

            filename = sanitize_filename("validation", reservation_id, "tmp", key)
            filepath = save_file(file, reservation_folder, filename)
            if not filepath:
                raise BadRequest(f"Failed to save {key}")

            validation_result = validate_document(filepath)
            validation_results[key] = validation_result
            if not validation_result.get("valid", False):
                invalid_files.append({
                    "field": key,
                    "reason": validation_result.get("error", "Invalid document"),
                    "confidence": validation_result.get("confidence", 0.0),
                })

        selfie_error = _validate_upload_file(files_payload["selfie"], "selfie")
        if selfie_error:
            raise BadRequest(selfie_error)
    finally:
        try:
            for filename in os.listdir(reservation_folder):
                os.remove(os.path.join(reservation_folder, filename))
            os.rmdir(reservation_folder)
        except OSError:
            pass

    return validation_results, invalid_files

def _get_gender_display(sesso):
    """Convert gender code to display string."""
    if sesso == '1':
        return 'Male'
    if sesso == '2':
        return 'Female'
    return 'N/A'

@upload_bp.route('/upload', methods=['POST'])
@log_route(include_request_data=False, include_response_data=False)
@log_database_operation("CREATE")
@log_performance(threshold_ms=3000)
@limiter.limit("10 per minute")
def upload_file():
    """
    Handle POST uploads of identity documents for a reservation.

    Accepts three image files in the request.files ('frontimage', 'backimage', 'selfie') and form fields including reservationId, name, surname, birthday, street, city, province, cap, telephone, document_type, document_number, and cf. Saves files under uploads/<reservationId>, runs OCR validation on front/back images, creates or updates the client record, links the client to the reservation, and returns a JSON response with saved filenames, per-file OCR validation results, client summary, and reservation summary.

    Side effects:
    - Persists uploaded files to disk.
    - Creates/updates client and links it to the reservation in the database.
    - Attempts to send an admin notification email (best-effort; failures do not affect the main operation).

    Responses:
    - 200: JSON with message, files, validation, client, and reservation data on success.
    - 400: Missing/invalid files or required form fields (BadRequest).
    - 404: Reservation not found or missing files referenced on disk.
    - 500: Internal server error for unexpected failures.
    """
    try:
        # Required files and form fields
        required_files = ['frontimage', 'backimage', 'selfie']
        required_fields = ['reservationId', 'name', 'surname', 'birthday', 'street', 'number_city',
                           'cap', 'telephone', 'document_type', 'document_number', 'cf']

        # Portale Alloggi required fields
        portale_required_fields = ['sesso', 'nazionalita', 'email', 'comune_nascita',
                                  'provincia_nascita', 'stato_nascita', 'cittadinanza',
                                  'luogo_emissione', 'data_emissione', 'data_scadenza',
                                  'autorita_rilascio', 'comune_residenza', 'provincia_residenza', 'stato_residenza']

        # Check if required files are in request
        if any(file_key not in request.files for file_key in required_files):
            raise BadRequest("Missing one or more required image files")

        # Extract form data
        all_required_fields = required_fields + portale_required_fields
        form_data = {field: request.form.get(field) for field in all_required_fields}
        if any(value is None for value in form_data.values()):
            raise BadRequest("Missing one or more required fields")

        reservation_id = str(form_data['reservationId'])

        # Require a signed upload token tied to reservation reference to prevent anonymous uploads.
        upload_token = request.headers.get("X-Upload-Token") or request.form.get("uploadToken")
        if not upload_token:
            return jsonify({"error": "Missing upload token"}), 401

        serializer = _build_serializer()
        payload, upload_error = _parse_upload_token(serializer, upload_token)
        if upload_error:
            return upload_error

        if str(payload.get("reservation_ref", "")) != reservation_id:
            return jsonify({"error": "Upload token does not match reservation"}), 403

        validation_token = (
            request.headers.get("X-Document-Validation-Token")
            or request.form.get("documentValidationToken")
        )
        skip_ocr = False
        if validation_token:
            try:
                validation_payload = serializer.loads(
                    validation_token,
                    salt=DOCUMENT_VALIDATION_TOKEN_SALT,
                    max_age=DOCUMENT_VALIDATION_TOKEN_MAX_AGE_SECONDS,
                )
                if str(validation_payload.get("reservation_ref", "")) != reservation_id:
                    return jsonify({"error": "Document validation token does not match reservation"}), 403
                skip_ocr = True
            except SignatureExpired:
                return jsonify({"error": "Document validation token expired"}), 401
            except BadSignature:
                return jsonify({"error": "Invalid document validation token"}), 401

        # Validate Portale Alloggi specific fields
        try:
            # Validate gender (sesso)
            if form_data['sesso'] not in ['1', '2']:
                raise BadRequest("Invalid gender value. Must be 1 (Male) or 2 (Female)")

            # Validate email format
            if form_data['email'] and '@' not in form_data['email']:
                raise BadRequest("Invalid email format")

            # Validate date formats
            if form_data['data_emissione']:
                datetime.strptime(form_data['data_emissione'], '%Y-%m-%d')
            if form_data['data_scadenza']:
                datetime.strptime(form_data['data_scadenza'], '%Y-%m-%d')

        except ValueError as e:
            raise BadRequest(f"Invalid date format: {str(e)}") from e

        cf = form_data['cf']
        # Create a folder for the reservation if it doesn't exist
        reservation_folder = os.path.join(UPLOAD_FOLDER, reservation_id)
        os.makedirs(reservation_folder, exist_ok=True)

        files = {}
        validation_results = {}

        # Check reservation existence before OCR-heavy processing
        reservation = get_reservation_by_id(reservation_id)
        if not reservation:
            return jsonify({"error": "Reservation not found"}), 404

        # Process images
        invalid_files = []
        for key in ['frontimage', 'backimage']:
            file = request.files[key]
            file_error = _validate_upload_file(file, key)
            if file_error:
                raise BadRequest(file_error)

            filename = sanitize_filename(form_data['name'], form_data['surname'], cf, key)
            filepath = save_file(file, reservation_folder, filename)
            if not filepath:
                raise BadRequest(f"Failed to save {key}")
            files[key] = filename

            # Validate document text
            if skip_ocr:
                validation_results[key] = {"valid": True, "skipped": True}
            else:
                validation_result = validate_document(filepath)
                validation_results[key] = validation_result
                if not validation_result.get("valid", False):
                    invalid_files.append({
                        "field": key,
                        "reason": validation_result.get("error", "Invalid document"),
                        "confidence": validation_result.get("confidence", 0.0),
                    })

        if invalid_files:
            return jsonify({
                "error": "Document validation failed",
                "retryable": True,
                "invalid_files": invalid_files,
                "validation": validation_results,
            }), 422

        # Process selfie
        selfie = request.files['selfie']
        selfie_error = _validate_upload_file(selfie, "selfie")
        if selfie_error:
            raise BadRequest(selfie_error)

        selfie_filename = sanitize_filename(form_data['name'], form_data['surname'], cf, "selfie")
        selfie_path = save_file(selfie, reservation_folder, selfie_filename)
        if not selfie_path:
            raise BadRequest("Failed to save selfie")
        files['selfie'] = selfie_filename

        client = get_client_by_cf(cf)
        client = add_or_update_client(form_data, client)
        link_client_to_reservation(reservation.id, client.id)

        # Send admin notification about completed check-in
        try:
            # Get admin email configuration
            email_config, admin_user = get_admin_email_config(reservation)

            if email_config:
                # Prepare check-in data for admin notification
                checkin_data = {
                    'reservation_number': reservation.id_reference,
                    'guest_name': reservation.name_reference,
                    'start_date': reservation.start_date.strftime('%Y-%m-%d') if reservation.start_date else 'N/A',
                    'end_date': reservation.end_date.strftime('%Y-%m-%d') if reservation.end_date else 'N/A',
                    'room_name': reservation.room.name if reservation.room else 'N/A',
                    'client_name': client.name,
                    'client_surname': client.surname,
                    'client_email': client.email or form_data.get('email', 'N/A'),
                    'client_phone': client.telephone,
                    'document_type': client.document_type,
                    'document_number': client.document_number,
                    'has_front_image': 'frontimage' in files,
                    'has_back_image': 'backimage' in files,
                    'has_selfie': 'selfie' in files,
                    # Portale Alloggi fields for admin notification
                    'client_gender': _get_gender_display(client.sesso),
                    'client_nationality': client.nazionalita or 'N/A',
                    'client_birth_municipality': client.comune_nascita or 'N/A',
                    'client_birth_province': client.provincia_nascita or 'N/A',
                    'client_birth_country': client.stato_nascita or 'N/A',
                    'client_citizenship': client.cittadinanza or 'N/A',
                    'client_document_issue_place': client.luogo_emissione or 'N/A',
                    'client_document_issue_date': client.data_emissione.strftime('%Y-%m-%d') if client.data_emissione else 'N/A',
                    'client_document_expiry_date': client.data_scadenza.strftime('%Y-%m-%d') if client.data_scadenza else 'N/A',
                    'client_issuing_authority': client.autorita_rilascio or 'N/A',
                    'client_residence_municipality': client.comune_residenza or 'N/A',
                    'client_residence_province': client.provincia_residenza or 'N/A',
                    'client_residence_country': client.stato_residenza or 'N/A'
                }

                # Send admin notification
                encryption_key = get_encryption_key()
                email_service = EmailService(config=email_config, encryption_key=encryption_key)

                # Use admin's email from user table or email config default sender
                admin_email = None
                if hasattr(admin_user, 'email') and admin_user.email:
                    admin_email = admin_user.email
                elif email_config.mail_default_sender_email:
                    admin_email = email_config.mail_default_sender_email

                # Only attempt to send email if we have a valid admin email
                if admin_email:
                    email_result = email_service.send_admin_checkin_notification(admin_email, checkin_data)

                    if email_result.get('status') == 'success':
                        logger.info("Admin notification sent successfully", extra=safe_extra_fields({
                            'admin_email': admin_email,
                            'reservation_id': reservation_id,
                            'client_name': f"{form_data['name']} {form_data['surname']}",
                            'notification_result': 'success'
                        }))
                    else:
                        logger.warning("Admin notification failed", extra=safe_extra_fields({
                            'admin_email': admin_email if 'admin_email' in locals() else 'unknown',
                            'error_message': email_result.get('message', 'Unknown error') if email_result else 'Unknown error',
                            'notification_result': 'failed'
                        }))
                else:
                    logger.warning("No valid admin email address found", extra=safe_extra_fields({
                        'admin_user_id': admin_user.id if admin_user else None,
                        'notification_result': 'skipped'
                    }))
            else:
                logger.warning("No email configuration found for admin", extra=safe_extra_fields({
                    'admin_user_id': admin_user.id if admin_user else None,
                    'notification_result': 'no_config'
                }))

        except Exception as e:
            # Don't fail the upload if email notification fails
            log_notification_error(logger, "admin notification", {
                'reservation_id': reservation_id,
                'client_name': f"{form_data['name']} {form_data['surname']}"
            }, e)

        return jsonify({
            "message": "Files uploaded successfully and client linked to reservation",
            "files": files,
            "validation": validation_results,
            "client": client.to_dict(),  # Use the model's to_dict() method which includes all Portale Alloggi fields
            "reservation": {
                "reservation_id": reservation.id,
                "id_reference": reservation.id_reference,
                "start_date": reservation.start_date,
                "end_date": reservation.end_date
            }
        }), 200

    except BadRequest as e:
        # Catch and handle specific BadRequest errors (file or form validation)
        return jsonify({"error": getattr(e, "description", None) or str(e)}), 400

    except FileNotFoundError:
        # Handle file not found errors
        return jsonify({"error": "File not found"}), 404

    except Exception:
        # General exception for unexpected errors
        logger.exception("Unexpected error during reservation upload")
        return jsonify({"error": "Internal server error"}), 500


@upload_bp.route('/upload/validate-documents', methods=['POST'])
@log_route(include_request_data=False, include_response_data=False)
@log_database_operation("READ")
@log_performance(threshold_ms=2000)
@limiter.limit("20 per minute")
def validate_upload_documents():
    """Pre-validate uploaded documents with OCR before full form submission."""
    try:
        required_files = ['frontimage', 'backimage', 'selfie']
        if any(file_key not in request.files for file_key in required_files):
            raise BadRequest("Missing one or more required image files")

        reservation_id = str(request.form.get("reservationId", "")).strip()
        if not reservation_id:
            raise BadRequest("Missing reservationId")

        serializer = _build_serializer()
        upload_token = request.headers.get("X-Upload-Token") or request.form.get("uploadToken")
        payload, upload_error = _parse_upload_token(serializer, upload_token)
        if upload_error:
            return upload_error
        if str(payload.get("reservation_ref", "")) != reservation_id:
            return jsonify({"error": "Upload token does not match reservation"}), 403

        reservation = get_reservation_by_id(reservation_id)
        if not reservation:
            return jsonify({"error": "Reservation not found"}), 404

        files_payload = {file_key: request.files[file_key] for file_key in required_files}
        validation_results, invalid_files = _validate_documents_payload(reservation_id, files_payload)
        if invalid_files:
            return jsonify({
                "error": "Document validation failed",
                "retryable": True,
                "invalid_files": invalid_files,
                "validation": validation_results,
            }), 422

        validation_token = serializer.dumps(
            {"reservation_ref": reservation_id},
            salt=DOCUMENT_VALIDATION_TOKEN_SALT,
        )
        return jsonify({
            "message": "Document validation successful",
            "validation": validation_results,
            "document_validation_token": validation_token,
        }), 200
    except BadRequest as e:
        return jsonify({"error": getattr(e, "description", None) or str(e)}), 400
    except Exception:
        logger.exception("Unexpected error during document pre-validation")
        return jsonify({"error": "Internal server error"}), 500
