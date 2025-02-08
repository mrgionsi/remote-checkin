# routes/room_routes.py
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from database import get_db  # Use absolute import
from models import Room

room_bp = Blueprint("room", __name__, url_prefix="/api/v1")

# Add a new room
@room_bp.route("/rooms", methods=["POST"])
def add_room():
    with get_db() as db:  # Using the 'with' statement to manage the database session
        data = request.get_json()

        # Validate the input data
        if not data.get("name") or not data.get("id_structure") or not data.get("capacity"):
            return jsonify({"error": "Missing required fields: 'name', 'capacity', or 'id_structure'"}), 400

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
    with get_db() as db:  # Using 'with' to properly manage the db session
        id_structure = 1  # Get structure ID from query params. For now, this value is fixed.

        if id_structure:
            rooms = db.query(Room).filter(Room.id_structure == id_structure).all()
        else:
            rooms = db.query(Room).all()  # Return all rooms if no structure is specified

        return jsonify([room.to_dict() for room in rooms])


# Get room by ID
@room_bp.route("/rooms/<int:room_id>", methods=["GET"])
def get_room(room_id):
    with get_db() as db:  # Using 'with' statement here as well
        room = db.query(Room).filter(Room.id == room_id).first()
        if room:
            return jsonify(room.to_dict())
        return jsonify({"error": "Room not found"}), 404


# Delete a room
@room_bp.route("/rooms/<int:room_id>", methods=["DELETE"])
def delete_room(room_id):
    with get_db() as db:  # Again, using 'with' for context management
        room = db.query(Room).filter(Room.id == room_id).first()

        if room:
            db.delete(room)
            db.commit()
            return jsonify({"message": "Room deleted successfully"}), 200

        return jsonify({"error": "Room not found"}), 404
