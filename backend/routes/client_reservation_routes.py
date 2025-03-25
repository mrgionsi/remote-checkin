# pylint: disable=C0301,E0611,E0401,W0718,R0914

"""
Client Reservations API Blueprint

This module defines a Flask Blueprint (`client_reservation_bp`) that handles operations related to 
clients and their reservations, including retrieving client details and managing uploaded images.

Endpoints:
-----------
1. GET /api/v1/reservations/<int:reservation_id>/clients
   - Retrieves all clients associated with a given reservation ID.
   - Returns a list of client details in JSON format.
   - Returns 404 if no clients are found.

2. POST /api/v1/reservations/<int:reservation_id>/client-images
   - Checks for the existence of a client's identity images (front, back, selfie) for a reservation.
   - Requires `name`, `surname`, `cf` (Codice Fiscale), and `reservationId` in the request body.
   - Returns URLs to existing images or indicates missing images.

3. GET /api/v1/images/<int:reservation_id>/<path:filename>
   - Serves client identity images from the `uploads/` directory.
   - Returns the requested image if it exists, or a 404 error if not found.

Configuration:
--------------
- `UPLOAD_FOLDER`: Directory where client identity images are stored (`uploads/`).

Dependencies:
-------------
- Flask (`Blueprint`, `jsonify`, `request`, `send_from_directory`)
- SQLAlchemy (`SessionLocal`)
- Models: `Client`, `ClientReservations`
- OS module for file path operations.

Usage:
------
- Include this blueprint in a Flask app to manage client reservations and identity images.

"""

import os
from flask import Blueprint, jsonify, request, send_from_directory
from models import Client, ClientReservations
from database import SessionLocal

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
    # Verify client belongs to this reservation
    db = SessionLocal()
    try:
        client_exists = db.query(Client).join(
            ClientReservations, Client.id == ClientReservations.id_client
        ).filter(
            ClientReservations.id_reservation == reservation_id,
            Client.name == name,
            Client.surname == surname,
            Client.cf == cf
        ).first()
        if not client_exists:
            return jsonify({"error": "Client not associated with this reservation"}), 404
    finally:
        db.close()

    folder_path = os.path.join(UPLOAD_FOLDER, str(reservation_id))

    if not os.path.exists(folder_path):
        return jsonify({"error": f"Folder for reservation {reservation_id} not found"}), 404




    # Expected filenames
    # Use sanitized versions of name, surname, and CF to prevent path traversal
    sanitized_name = "".join(c for c in name if c.isalnum() or c in [' ', '-', '_']).strip()
    sanitized_surname = "".join(c for c in surname if c.isalnum() or c in [' ', '-', '_']).strip()
    sanitized_cf = "".join(c for c in cf if c.isalnum()).strip()
    file_base = f"{sanitized_name}-{sanitized_surname}-{sanitized_cf}"

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
            result[key] = f"/api/v1/images/{reservation_id}/{file_name}"
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
