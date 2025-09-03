"""
This module handles the routes for uploading identity documents related to reservations.
It processes image files, validates them using OCR, and links the uploaded files with
the corresponding client and reservation in the database.

Functions:
- upload_file: Handles the upload of the front and back identity document images and selfies.
"""


#pylint: disable=C0301,E0401,R0914,W0718,W0612
import os
from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest
from utils.file_utils import allowed_file, sanitize_filename, save_file
from utils.ocr_utils import validate_document
from utils.db_utils import get_reservation_by_id, get_client_by_cf, add_or_update_client, link_client_to_reservation

upload_bp = Blueprint('upload', __name__, url_prefix="/api/v1")
UPLOAD_FOLDER = 'uploads/'

@upload_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    Upload and validate identity documents for a reservation.
    """
    try:
        # Required files and form fields
        required_files = ['frontimage', 'backimage', 'selfie']
        required_fields = ['reservationId', 'name', 'surname', 'birthday', 'street',
                           'city', 'province', 'cap', 'telephone', 'document_type', 'document_number', 'cf']        

        # Check if required files are in request
        if any(file_key not in request.files for file_key in required_files):
            raise BadRequest("Missing one or more required image files")

        # Extract form data
        form_data = {field: request.form.get(field) for field in required_fields}
        if any(value is None for value in form_data.values()):
            raise BadRequest("Missing one or more required fields")

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
            from models import EmailConfig, User, Structure, Room
            from email_handler import EmailService
            from routes.email_config_routes import get_encryption_key
            from database import SessionLocal as EmailSessionLocal
            
            # Get admin email configuration
            email_session = EmailSessionLocal()
            try:
                # Get the structure admin using AdminStructure relationship
                from models import AdminStructure
                admin_structure = email_session.query(AdminStructure).filter(
                    AdminStructure.id_structure == reservation.room.id_structure
                ).first()
                
                admin_user = None
                if admin_structure:
                    admin_user = email_session.query(User).filter(
                        User.id == admin_structure.id_user
                    ).first()
                
                if admin_user:
                    # Get admin's email configuration
                    email_config = email_session.query(EmailConfig).filter(
                        EmailConfig.user_id == admin_user.id,
                        EmailConfig.is_active == True
                    ).first()
                    
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
                            'client_email': form_data.get('email', 'N/A'),
                            'client_phone': client.telephone,
                            'document_type': client.document_type,
                            'document_number': client.document_number,
                            'has_front_image': 'frontimage' in files,
                            'has_back_image': 'backimage' in files,
                            'has_selfie': 'selfie' in files
                        }
                        
                        # Send admin notification
                        encryption_key = get_encryption_key()
                        email_service = EmailService(config=email_config, encryption_key=encryption_key)
                        
                        # Use admin's email from user table, email config, or fallback
                        admin_email = None
                        if hasattr(admin_user, 'email') and admin_user.email:
                            admin_email = admin_user.email
                        elif email_config.mail_default_sender_email:
                            admin_email = email_config.mail_default_sender_email
                        else:
                            admin_email = email_config.mail_username  # Fallback to SMTP username
                        
                        if admin_email:
                            email_result = email_service.send_admin_checkin_notification(admin_email, checkin_data)
                            
                            if email_result.get('status') == 'success':
                                print(f"Admin notification sent successfully to {admin_email}")
                            else:
                                print(f"Failed to send admin notification: {email_result.get('message', 'Unknown error')}")
                        else:
                            print("No valid admin email address found")
                    else:
                        print(f"No email configuration found for admin user {admin_user.id}")
                else:
                    print(f"No admin user found for structure {reservation.room.id_structure}")
                    
            finally:
                email_session.close()
                
        except Exception as e:
            # Don't fail the upload if email notification fails
            print(f"Error sending admin notification: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")

        return jsonify({
            "message": "Files uploaded successfully and client linked to reservation",
            "files": files,
            "validation": validation_results,
            "client": {
                "id": client.id,
                "name": client.name,
                "surname": client.surname,
                "birthday": client.birthday,
                "street": client.street,
                "city": client.city,
                "province": client.province,
                "cap": client.cap,
                "telephone": client.telephone,
                "document_number": client.document_number,
                "cf": client.cf
            },
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
