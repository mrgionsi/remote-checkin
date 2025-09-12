"""
This module handles the routes for uploading identity documents related to reservations.
It processes image files, validates them using OCR, and links the uploaded files with
the corresponding client and reservation in the database.

Functions:
- upload_file: Handles the upload of the front and back identity document images and selfies.
"""


#pylint: disable=C0301,E0401,R0914,W0718,W0612,E0611,R0912,R0915,R1702
import os
import traceback

from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest

from utils.file_utils import allowed_file, sanitize_filename, save_file
from utils.ocr_utils import validate_document
from utils.db_utils import get_reservation_by_id, get_client_by_cf, add_or_update_client, link_client_to_reservation
from utils.email_utils import get_admin_email_config
from email_handler import EmailService
from routes.email_config_routes import get_encryption_key

upload_bp = Blueprint('upload', __name__, url_prefix="/api/v1")
UPLOAD_FOLDER = 'uploads/'

@upload_bp.route('/upload', methods=['POST'])
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
        required_fields = ['reservationId', 'name', 'surname', 'birthday', 'street',
                           'city', 'province', 'cap', 'telephone', 'document_type', 'document_number', 'cf']
        
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
        
        # Validate Portale Alloggi specific fields
        try:
            # Validate gender (sesso)
            if form_data['sesso'] not in ['1', '2']:
                raise BadRequest("Invalid gender value. Must be 1 (Male) or 2 (Female)")
            
            # Validate email format
            if form_data['email'] and '@' not in form_data['email']:
                raise BadRequest("Invalid email format")
                
            # Validate date formats
            from datetime import datetime
            if form_data['data_emissione']:
                datetime.strptime(form_data['data_emissione'], '%Y-%m-%d')
            if form_data['data_scadenza']:
                datetime.strptime(form_data['data_scadenza'], '%Y-%m-%d')
                
        except ValueError as e:
            raise BadRequest(f"Invalid date format: {str(e)}")
        except Exception as e:
            raise BadRequest(f"Validation error: {str(e)}")

        reservation_id = form_data['reservationId']
        cf = form_data['cf']
        # Create a folder for the reservation if it doesn't exist
        reservation_folder = os.path.join(UPLOAD_FOLDER, reservation_id)
        os.makedirs(reservation_folder, exist_ok=True)

        files = {}
        validation_results = {}

        # Process images
        for key in ['frontimage', 'backimage']:
            file = request.files[key]
            if file and allowed_file(file.filename):
                filename = sanitize_filename(form_data['name'], form_data['surname'], cf, key)
                filepath = save_file(file, reservation_folder, filename)
                files[key] = filename

                # Validate document text
                is_valid, text = validate_document(filepath)
                validation_results[key] = {"valid": is_valid, "extracted_text": text}
                if not is_valid:
                    raise BadRequest(f"Invalid document for {key}")
            else:
                raise BadRequest(f"Invalid file type for {key}")

        # Process selfie
        selfie = request.files['selfie']
        if selfie and allowed_file(selfie.filename):
            selfie_filename = sanitize_filename(form_data['name'], form_data['surname'], cf, "selfie")
            selfie_filepath = save_file(selfie, reservation_folder, selfie_filename)
            files['selfie'] = selfie_filename
        else:
            raise BadRequest("Invalid file type for selfie")

        # Handle client and reservation
        reservation = get_reservation_by_id(reservation_id)
        if not reservation:
            return jsonify({"error": "Reservation not found"}), 404

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
                    'client_gender': 'Male' if client.sesso == 1 else 'Female' if client.sesso == 2 else 'N/A',
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
                        print(f"Admin notification sent successfully to {admin_email}")
                    else:
                        print(f"Failed to send admin notification: {email_result.get('message', 'Unknown error')}")
                else:
                    print("No valid admin email address found - skipping notification")
            else:
                print(f"No email configuration found for admin user {admin_user.id if admin_user else 'None'}")

        except Exception as e:
            # Don't fail the upload if email notification fails
            print(f"Error sending admin notification: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")

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
        return jsonify({"error": str(e)}), 400

    except FileNotFoundError as e:
        # Handle file not found errors
        return jsonify({"error": f"File not found: {str(e)}"}), 404

    except Exception as e:
        # General exception for unexpected errors
        return jsonify({"error": "Internal server error", "details": str(e)}), 500
