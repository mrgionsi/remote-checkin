# routes/room_routes.py
# pylint: disable=C0301
"""
This module contains the API routes for managing rooms in the system.

It defines the following endpoints:

- POST /api/v1/rooms: Adds a new room to the database.
- GET /api/v1/rooms: Retrieves a list of rooms for a fixed structure (currently structure ID 1).
- GET /api/v1/rooms/<room_id>: Retrieves a specific room by its unique identifier.
- DELETE /api/v1/rooms/<room_id>: Deletes a room from the database by its unique identifier.

Each route interacts with the database to perform the necessary actions related to rooms.
"""

from flask import Blueprint, request, jsonify
#pylint: disable=E0611,E0401
from models import Room
from database import get_db  # Use absolute import

room_bp = Blueprint("room", __name__, url_prefix="/api/v1")


# Add a new room
@room_bp.route("/rooms", methods=["POST"])
def add_room():
    """
    Add a new room to the database.

    This API endpoint reads JSON data from the incoming request and validates that the required fields "name",
    "id_structure", and "capacity" are provided. 
    If any of these fields are missing, the function returns a JSON error message with a 400 status code. 
    If all required data is present, a new Room instance is created, added to the database, and committed.
    The newly created room is then returned as a JSON object with a 201 status code.

    Returns:
        tuple: A tuple containing:
            - A Flask Response object with the JSON representation of the room (or an error message).
            - An HTTP status code (201 for success, 400 if validation fails).
    """
    with get_db() as db:  # Using the 'with' statement to manage the database session
        data = request.get_json()

        # Validate the input data
        if (
            not data.get("name")
            or not data.get("id_structure")
            or not data.get("capacity")
        ):
            return jsonify(
                {
                    "error": "Missing required fields: 'name', 'capacity', or 'id_structure'"
                }
            ), 400

        # Create a new room
        new_room = Room(
            name=data["name"],
            capacity=data["capacity"],
            id_structure=data["id_structure"],
        )

        # Add to DB and commit
        db.add(new_room)
        db.commit()
        db.refresh(new_room)

        return jsonify(new_room.to_dict()), 201


# Get all rooms by structure
@room_bp.route("/rooms", methods=["GET"])
def get_rooms():
    """
    Retrieve a list of rooms for a fixed structure.

    This function opens a database session and queries for room records. It applies a filter
    using a fixed structure ID (currently set to 1) and retrieves all rooms that belong to that
    structure. If no valid structure ID is provided, it returns all available rooms. Each room
    object is converted to a dictionary via its to_dict() method, and the resulting list is
    returned as a JSON response.

    Returns:
        flask.Response: A JSON response containing a list of room dictionaries.
    """
    with get_db() as db:  # Using 'with' to properly manage the db session
        id_structure = (
            1  # Get structure ID from query params. For now, this value is fixed.
        )

        if id_structure:
            rooms = db.query(Room).filter(Room.id_structure == id_structure).all()
        else:
            rooms = db.query(
                Room
            ).all()  # Return all rooms if no structure is specified

        return jsonify([room.to_dict() for room in rooms])


# Get room by ID
@room_bp.route("/rooms/<int:room_id>", methods=["GET"])
def get_room(room_id):
    """
    Retrieve a room by its unique identifier.

    This function queries the database for a room with the specified room_id using a context-managed database session. If the room is found, its details are returned as a JSON response. Otherwise, a JSON response with an error message and a 404 HTTP status code is returned.

    Parameters:
        room_id (int): The unique identifier of the room to retrieve.

    Returns:
        A Flask response object:
            - On success: JSON containing room details (dictionary format) and a 200 HTTP status code.
            - On failure: JSON with an error message and a 404 HTTP status code if no room is found.
    """
    with get_db() as db:  # Using 'with' statement here as well
        room = db.query(Room).filter(Room.id == room_id).first()
        if room:
            return jsonify(room.to_dict())
        return jsonify({"error": "Room not found"}), 404


# Delete a room
@room_bp.route("/rooms/<int:room_id>", methods=["DELETE"])
def delete_room(room_id):
    """
    Delete a room from the database based on the provided room_id.

    This function queries the database for a room with the given room_id. If the room exists, it deletes the room, commits the transaction,
    and returns a JSON response with a success message and HTTP status code 200. If the room is not found, it returns a JSON response with
    an error message and HTTP status code 404.

    Parameters:
        room_id (int): The unique identifier of the room to be deleted.

    Returns:
        tuple: A tuple containing a JSON response and an HTTP status code.
    """
    with get_db() as db:  # Again, using 'with' for context management
        room = db.query(Room).filter(Room.id == room_id).first()

        if room:
            db.delete(room)
            db.commit()
            return jsonify({"message": "Room deleted successfully"}), 200

        return jsonify({"error": "Room not found"}), 404
