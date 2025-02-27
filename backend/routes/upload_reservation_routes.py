from datetime import datetime
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
import cv2
import pytesseract
from sqlalchemy.exc import SQLAlchemyError

from database import get_db
from models import Client, ClientReservations, Reservation

# Define blueprint for the upload API
upload_bp = Blueprint('upload', __name__, url_prefix="/api/v1")

# Upload folder configuration
UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Ensure the upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """
    Check if the uploaded file has an allowed extension.
    
    Parameters:
        filename (str): The name of the uploaded file.
    
    Returns:
        bool: True if file extension is allowed, False otherwise.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_document(image_path):
    """
    Validate the document by extracting text using OCR.

    Parameters:
        image_path (str): The file path of the uploaded document.

    Returns:
        tuple: (bool, str) where bool indicates validity and str contains extracted text.
    """
    # Load the image
    image = cv2.imread(image_path)

    # ✅ Check if the image was loaded successfully
    if image is None:
        return False, "Error: Could not load image. File may be corrupted or unsupported format."

    # Convert to grayscale for better OCR accuracy
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Extract text using OCR
    text = pytesseract.image_to_string(gray)

    # Check if extracted text is valid
    return (True, text) if len(text.strip()) > 10 else (False, "No valid text detected")

@upload_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    Upload and validate identity documents for a reservation.
    
    This function handles the file upload process for front and back images of an ID, along with a selfie.
    It validates the images, extracts text using OCR, and updates or creates client records in the database.
    
    Returns:
        Flask Response: JSON response indicating success or failure.
    """
    try:
        # Required files and form fields
        required_files = ['frontImage', 'backImage', 'selfie']
        required_fields = ['reservationId', 'name', 'surname', 'birthday', 'street', 'city', 'province', 'cap', 'telephone', 'document_type', 'document_number', 'cf']
        
        # Check if required files are in request
        if any(file_key not in request.files for file_key in required_files):
            return jsonify({"error": "Missing one or more required image files"}), 400

        # Extract form data
        form_data = {field: request.form.get(field) for field in required_fields}
        
        # Ensure all required fields are present
        if any(value is None for value in form_data.values()):
            return jsonify({"error": "Missing one or more required fields"}), 400

        reservation_id = form_data['reservationId']
        print(reservation_id)
        cf = form_data['cf']
        
        # Create a folder for the reservation if it doesn't exist
        reservation_folder = os.path.join(UPLOAD_FOLDER, reservation_id)
        os.makedirs(reservation_folder, exist_ok=True)

        files = {}
        validation_results = {}

        # Process frontImage and backImage with validation
        for key in ['frontImage', 'backImage']:
            file = request.files[key]
            if file and allowed_file(file.filename):
                filename = f"{form_data['name']}-{form_data['surname']}-{cf}-{key}.jpg"
                filepath = os.path.join(reservation_folder, filename)
                file.save(filepath)
                files[key] = filename

                # Validate document text
                is_valid, text = validate_document(filepath)
                validation_results[key] = {"valid": is_valid, "extracted_text": text}
                if not is_valid:
                    return jsonify({"error": f"Invalid document for {key}"}), 400
            else:
                return jsonify({"error": f"Invalid file type for {key}"}), 400

        # Process selfie without validation
        selfie = request.files['selfie']
        if selfie and allowed_file(selfie.filename):
            selfie_filename = f"{form_data['name']}-{form_data['surname']}-{cf}-selfie.jpg"
            selfie_filepath = os.path.join(reservation_folder, selfie_filename)
            selfie.save(selfie_filepath)
            files['selfie'] = selfie_filename
        else:
            return jsonify({"error": "Invalid file type for selfie"}), 400

        # Insert or update client data in the database
        with get_db() as db:
            # Verify reservation exists
            reservation = db.query(Reservation).filter(Reservation.id_reference == reservation_id).first()
            if not reservation:
                return jsonify({"error": "Reservation not found"}), 404

            # Check if client exists by CF
            client = db.query(Client).filter(Client.cf == cf).first()

            if client:
                # Update existing client
                for key, value in form_data.items():
                    if hasattr(client, key) and key != 'reservationId':
                        setattr(client, key, value if (key != 'birthday' or 'reservationId') else datetime.strptime(value, "%Y-%m-%d"))
            else:
                # Create new client
                client = Client(**{**form_data, 'birthday': datetime.strptime(form_data['birthday'], "%Y-%m-%d")})
                db.add(client)

            db.commit()
            db.refresh(client)

            # Link client to reservation if not already linked
            existing_link = db.query(ClientReservations).filter(
                ClientReservations.id_reservation == reservation.id,
                ClientReservations.id_client == client.id
            ).first()

            if not existing_link:
                client_reservation = ClientReservations(id_reservation=reservation.id, id_client=client.id)
                db.add(client_reservation)
                db.commit()
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

    except SQLAlchemyError as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500
