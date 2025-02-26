from datetime import datetime
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
import cv2
import pytesseract
from sqlalchemy.exc import SQLAlchemyError

from database import get_db
from models import Client, ClientReservations, Reservation

upload_bp = Blueprint('upload', __name__,url_prefix="/api/v1")

UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_document(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray)
    
    if len(text.strip()) > 10:
        return True, text  # A valid document should have readable text
    return False, "No valid text detected"

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
import cv2
import pytesseract

upload_bp = Blueprint('upload', __name__, url_prefix="/api/v1")

UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_document(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray)
    
    if len(text.strip()) > 10:
        return True, text  # A valid document should have readable text
    return False, "No valid text detected"


@upload_bp.route('/upload', methods=['POST'])
def upload_file():
    try:
        # Ensure the required image files are present
        required_files = ['frontImage', 'backImage', 'selfie']
        if any(file_key not in request.files for file_key in required_files):
            return jsonify({"error": "Missing file(s)"}), 400

        # Get additional form data from the request
        reservation_id = request.form.get('reservationId')
        name = request.form.get('name')
        surname = request.form.get('surname')
        birthday = request.form.get('birthday')
        street = request.form.get('street')
        number_city = request.form.get('number_city')
        city = request.form.get('city')
        province = request.form.get('province')
        cap = request.form.get('cap')
        telephone = request.form.get('telephone')
        document_type = request.form.get('document_type')
        document_number = request.form.get('document_number')
        cf = request.form.get('cf')

        # Validate required fields
        required_fields = [reservation_id, name, surname, birthday, street, city, province, cap, telephone, document_type, document_number, cf]
        if any(field is None for field in required_fields):
            return jsonify({"error": "Missing one or more required fields"}), 400

        # Create a folder for the reservation if it doesn't exist
        reservation_folder = os.path.join(UPLOAD_FOLDER, reservation_id)
        os.makedirs(reservation_folder, exist_ok=True)

        files = {}
        validation_results = {}

        # Process 'frontImage' and 'backImage' with validation
        for key in ['frontImage', 'backImage']:
            file = request.files[key]
            if file and allowed_file(file.filename):
                filename = f"{name}-{surname}-{cf}-{key}.{'jpg' if file.filename.lower().endswith('jpg') else 'png'}"
                filepath = os.path.join(reservation_folder, filename)
                file.save(filepath)
                files[key] = filename

                # Validate the document
                is_valid, text = validate_document(filepath)
                validation_results[key] = {"valid": is_valid, "extracted_text": text}
                if not is_valid:
                    return jsonify({"error": f"Invalid document for {key}"}), 400
            else:
                return jsonify({"error": f"Invalid file type for {key}"}), 400

        # Process 'selfie' without validation
        selfie = request.files['selfie']
        if selfie and allowed_file(selfie.filename):
            selfie_filename = f"{name}-{surname}-{cf}-selfie.{selfie.filename.rsplit('.', 1)[1].lower()}"
            selfie_filepath = os.path.join(reservation_folder, selfie_filename)
            selfie.save(selfie_filepath)
            files['selfie'] = selfie_filename
        else:
            return jsonify({"error": "Invalid file type for selfie"}), 400

        # Insert or update client data in the database
        with get_db() as db:
            # Check if the reservation exists
            reservation = db.query(Reservation).filter(Reservation.id_reference == reservation_id).first()
            if not reservation:
                return jsonify({"error": "Reservation not found"}), 404

            # Check if client already exists by CF
            client = db.query(Client).filter(Client.cf == cf).first()

            if client:
                # Update existing client
                client.name = name
                client.surname = surname
                client.birthday = datetime.strptime(birthday, "%Y-%m-%d")
                client.street = street
                client.number_city = number_city
                client.city = city
                client.province = province
                client.cap = cap
                client.telephone = telephone
                client.document_number = document_number
            else:
                # Create a new client
                client = Client(
                    name=name,
                    surname=surname,
                    birthday=datetime.strptime(birthday, "%Y-%m-%d"),
                    street=street,
                    number_city=number_city,
                    city=city,
                    province=province,
                    cap=cap,
                    telephone=telephone,
                    document_number=document_number,
                    cf=cf
                )
                db.add(client)

            db.commit()
            db.refresh(client)

            # Check if the client-reservation link already exists
            existing_link = db.query(ClientReservations).filter(
                ClientReservations.id_reservation == reservation.id,
                ClientReservations.id_client == client.id
            ).first()

            if not existing_link:
                # Create a new client-reservation link
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
