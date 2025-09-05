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

from pathlib import Path

from flask import Blueprint, jsonify, request, send_from_directory
from flask_jwt_extended import jwt_required, verify_jwt_in_request

from models import Client, ClientReservations, Reservation
from database import SessionLocal

# Blueprint setup
client_reservation_bp = Blueprint("client_reservations", __name__, url_prefix="/api/v1")

@client_reservation_bp.route("/reservations/<int:reservation_id>/clients", methods=["GET"])
@jwt_required()
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

# Resolve the base directory once for security
BASE_UPLOAD_DIR = Path(UPLOAD_FOLDER).resolve()

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks.
    Rejects filenames containing path separators or '..' segments.
    """
    if not filename:
        raise ValueError("Filename cannot be empty")

    # Check for path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        raise ValueError("Filename contains invalid characters")

    # Additional sanitization - remove any remaining dangerous characters
    sanitized = "".join(c for c in filename if c.isalnum() or c in '.-_').strip()
    if not sanitized:
        raise ValueError("Filename contains no valid characters")

    return sanitized

def get_secure_file_path(reservation_id: str, filename: str) -> Path:
    """
    Get a secure file path by resolving the base directory and filename.
    Ensures the resulting path is within the base upload directory.
    
    Args:
        reservation_id: The reservation ID (will be sanitized)
        filename: The filename (will be sanitized)

    Returns:
        Path: The resolved and validated file path

    Raises:
        ValueError: If path traversal is detected or filename is invalid
    """
    # Sanitize inputs
    safe_reservation_id = sanitize_filename(str(reservation_id))
    safe_filename = sanitize_filename(filename)

    # Build the path using pathlib
    target_path = BASE_UPLOAD_DIR / safe_reservation_id / safe_filename
    resolved_target = target_path.resolve()

    # Ensure the target is within the base directory
    try:
        resolved_target.relative_to(BASE_UPLOAD_DIR)
    except ValueError as exc:
        raise ValueError("Path traversal detected") from exc

    return resolved_target

def safe_file_exists(file_path: Path) -> bool:
    """
    Safely check if a file exists using os.stat to avoid TOCTOU issues.
    """
    try:
        return file_path.is_file()
    except (OSError, PermissionError):
        return False

@client_reservation_bp.route("/reservations/<string:reservation_id>/client-images", methods=["POST"])
@jwt_required()
def check_images(reservation_id):
    """
    Check whether identity images (back, front, selfie) exist for a given reservation and client.
    
    Validates required JSON fields ("name", "surname", "cf"), confirms the reservation (matched against Reservation.id_reference) and that the client is associated with that reservation, then inspects the reservation's upload folder (UPLOAD_FOLDER/<reservation_id>) for three expected files named `<name>-<surname>-<cf>-backimage.jpg`, `-frontimage.jpg`, and `-selfie.jpg` (name/surname/cf are sanitized). Returns a JSON object with keys "back_image", "front_image", and "selfie" mapped to the API URL for the file if present ("/api/v1/images/<reservation_id>/<filename>") or null if missing.
    
    Responses:
    - 200: JSON object with the three keys and URL or null values.
    - 400: Missing required fields in the request JSON.
    - 404: Reservation not found, client not associated with the reservation, or reservation upload folder not found.
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
        reservation = db.query(Reservation).filter(
        Reservation.id_reference == str(reservation_id)).first()
        if not reservation:
            return jsonify({"error": "Error fetching reservation, reservation doesn't exists"}), 404
        client_exists = db.query(Client).join(
            ClientReservations, Client.id == ClientReservations.id_client
        ).filter(
            ClientReservations.id_reservation == reservation.id,
            Client.name == name,
            Client.surname == surname,
            Client.cf == cf
        ).first()

        if not client_exists:
            return jsonify({"error": "Client not associated with this reservation"}), 404
    finally:
        db.close()

    # Expected filenames - use sanitized versions to prevent path traversal
    sanitized_name = "".join(c for c in name if c.isalnum() or c in [' ', '-', '_']).strip()
    sanitized_surname = "".join(c for c in surname if c.isalnum() or c in [' ', '-', '_']).strip()
    sanitized_cf = "".join(c for c in cf if c.isalnum()).strip()
    file_base = f"{sanitized_name}-{sanitized_surname}-{sanitized_cf}"
    file_names = {
        "back_image": f"{file_base}-backimage.jpg",
        "front_image": f"{file_base}-frontimage.jpg",
        "selfie": f"{file_base}-selfie.jpg",
    }

    # Check if files exist using secure path resolution
    result = {}
    for key, file_name in file_names.items():
        try:
            file_path = get_secure_file_path(reservation_id, file_name)
            if safe_file_exists(file_path):
                result[key] = f"/api/v1/images/{reservation_id}/{file_name}"
            else:
                result[key] = None  # File not found
        except ValueError:
            # If path traversal is detected, treat as file not found
            result[key] = None

    return jsonify(result)


@client_reservation_bp.route("/images/<string:reservation_id>/<path:filename>", methods=["GET", "OPTIONS"])
def get_image(reservation_id, filename):
    """
    Serve a client identity image file for a reservation or respond to CORS preflight.
    
    For GET requests this endpoint requires a valid JWT. If the reservation folder or requested file does not exist, returns a JSON 404 error. For OPTIONS requests it returns an empty JSON body with permissive CORS headers.
    
    Parameters:
        reservation_id (str): Reservation reference used to locate the uploads subfolder.
        filename (str): File name (including extension) inside the reservation folder.
    
    Returns:
        A Flask response containing the requested file on success, or a JSON error response with HTTP 404 when the folder or file is missing. OPTIONS requests return a 200 response with CORS headers.
    """
    # Handle OPTIONS request for CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    # For GET requests, require JWT authentication
    verify_jwt_in_request()

    try:
        # Use secure path resolution to prevent path traversal
        file_path = get_secure_file_path(reservation_id, filename)
        print(f"Looking for image: reservation_id={reservation_id}, filename={filename}")
        print(f"Resolved file path: {file_path}")

        if not safe_file_exists(file_path):
            print(f"File not found: {file_path}")
            return jsonify({"error": "Image not found"}), 404

        # Get the directory and filename for send_from_directory
        folder_path = str(file_path.parent)
        safe_filename = file_path.name

        # Set proper headers for image serving
        response = send_from_directory(folder_path, safe_filename)

    except ValueError as e:
        print(f"Path traversal detected: {e}")
        return jsonify({"error": "Invalid file path"}), 400
    except Exception as e:
        print(f"Error accessing file: {e}")
        return jsonify({"error": "Error accessing file"}), 500
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response
