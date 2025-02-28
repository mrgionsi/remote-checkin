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
from utils.file_utils import allowed_file, save_file
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
        required_files = ['frontImage', 'backImage', 'selfie']
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
        for key in ['frontImage', 'backImage']:
            file = request.files[key]
            if file and allowed_file(file.filename):
                filename = f"{form_data['name']}-{form_data['surname']}-{cf}-{key}.jpg"
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
            selfie_filename = f"{form_data['name']}-{form_data['surname']}-{cf}-selfie.jpg"
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
