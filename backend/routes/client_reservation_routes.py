import os
from flask import Blueprint, jsonify, request, send_from_directory
from sqlalchemy.orm import joinedload
from database import SessionLocal
from models import Client, ClientReservations

# Blueprint setup
client_reservation_bp = Blueprint("client_reservations", __name__, url_prefix="/api/v1")

@client_reservation_bp.route("/reservations/<int:reservation_id>/clients", methods=["GET"])
def get_clients_by_reservation(reservation_id):
    """
    Get all clients associated with a given reservation ID.

    Args:
        reservation_id (int): The ID of the reservation.

    Returns:
        flask.Response: JSON array containing client details or a 404 error if no clients found.
    """
    db = SessionLocal()
    try:
        # Get clients linked to the reservation
        client_reservations = (
            db.query(Client)
            .join(ClientReservations, Client.id == ClientReservations.id_client)
            .filter(ClientReservations.id_reservation == reservation_id)
            .all()
        )

        if not client_reservations:
            return jsonify({"error": f"No clients found for reservation ID {reservation_id}"}), 404

        return jsonify([client.to_dict() for client in client_reservations])

    except Exception as e:
        return jsonify({"error": f"Error retrieving clients: {str(e)}"}), 500
    finally:
        db.close()



UPLOAD_FOLDER = "uploads/"  # Base directory for uploaded images

@client_reservation_bp.route("/reservations/<int:reservation_id>/client-images", methods=["POST"])
def check_images(reservation_id):
    """
    Check if images exist for a given client and reservation ID.

    Request Body:
        - name (str): Client's first name.
        - surname (str): Client's last name.
        - cf (str): Client's CF (Codice Fiscale).
        - reservationId (int): The reservation ID.

    Returns:
        - JSON response with image URLs or error message.
    """
    data = request.get_json()
    
    name = data.get("name")
    surname = data.get("surname")
    cf = data.get("cf")

    if not all([name, surname, cf, reservation_id]):
        return jsonify({"error": "Missing required fields"}), 400

    folder_path = os.path.join(UPLOAD_FOLDER, str(reservation_id))
    
    if not os.path.exists(folder_path):
        return jsonify({"error": f"Folder for reservation {reservation_id} not found"}), 404

    # Expected filenames
    file_base = f"{name}-{surname}-{cf}"
    file_names = {
        "back_image": f"{file_base}-backimage.jpg",
        "front_image": f"{file_base}-frontimage.jpg",
        "selfie": f"{file_base}-selfie.jpg",
    }

   # Check if files exist and return API URLs
    result = {}
    for key, file_name in file_names.items():
        file_path = os.path.join(folder_path, file_name)
        if os.path.exists(file_path):
            result[key] = f"/api/v1/images/{reservation_id}/{file_name}"  # API URL for fetching the image
        else:
            result[key] = None  # File not found

    return jsonify(result)



@client_reservation_bp.route("/images/<int:reservation_id>/<path:filename>")
def get_image(reservation_id, filename):
    """
    Serve images from the uploads folder.

    Args:
        reservation_id (int): The reservation ID.
        filename (str): The image file name.

    Returns:
        - The image file if found.
        - 404 error if the file does not exist.
    """
    folder_path = os.path.join(UPLOAD_FOLDER, str(reservation_id))
    
    if not os.path.exists(folder_path):
        return jsonify({"error": "Reservation folder not found"}), 404
    
    file_path = os.path.join(folder_path, filename)
    
    if not os.path.exists(file_path):
        return jsonify({"error": "Image not found"}), 404

    return send_from_directory(folder_path, filename)