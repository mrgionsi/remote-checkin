# routes/room_routes.py
# pylint: disable=C0301
"""
This module contains the API routes for managing rooms in the system.

It defines the following endpoints:

- POST /api/v1/rooms: Adds a new room to the database.
- GET /api/v1/rooms: Retrieves a list of rooms for a fixed structure (currently structure ID 1).
- GET /api/v1/rooms/<room_id>: Retrieves a specific room by its unique identifier.
- PUT /api/v1/rooms/<room_id>: Updates an existing room's details.
- DELETE /api/v1/rooms/<room_id>: Deletes a room from the database by its unique identifier.

Each route interacts with the database to perform the necessary actions related to rooms.
"""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

#pylint: disable=E0611,E0401
from models import Room, Structure
from database import get_db  # Use absolute import
from app_logging.config import get_logger
from app_logging.decorators import log_route, log_database_operation, log_function
from app_logging.utils import safe_extra_fields

# Configure logging
logger = get_logger(__name__)

room_bp = Blueprint("room", __name__, url_prefix="/api/v1")


@log_function(include_args=True, include_result=True, max_arg_length=200)
def _validate_room_update_data(data, db):
    """Validate room update data and return error message if invalid."""
    if "name" in data and not data["name"].strip():
        return "Room name cannot be empty"
    if "capacity" in data:
        try:
            capacity = int(data["capacity"])
            if capacity <= 0:
                return "Capacity must be a positive number"
        except ValueError:
            return "Invalid capacity value"
    if "id_structure" in data:
        try:
            structure = db.query(Structure).filter(Structure.id == data["id_structure"]).first()
            if not structure:
                return "Invalid structure ID"
        except SQLAlchemyError as e:
            logger.error("Database error validating structure ID %s: %s", data["id_structure"], str(e))
            return "Failed to validate structure ID due to database error"
    return None


# Add a new room
@room_bp.route("/rooms", methods=["POST"])
@jwt_required()
@log_route(include_request_data=True)
@log_database_operation("CREATE")
def add_room():
    """
    Creates a new room using JSON data from the request and adds it to the database.

    Validates that "name", "id_structure", and "capacity" are present in the request body. Returns a JSON error message with status 400 if any required field is missing. On success, returns the created room as JSON with status 201.

    Returns:
        tuple: JSON response containing the new room or an error message, and the corresponding HTTP status code.
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
        try:
            db.add(new_room)
            db.commit()
            db.refresh(new_room)
            logger.info("Room created successfully", extra={
                'room_id': new_room.id,
                'room_name': new_room.name,
                'room_capacity': new_room.capacity,
                'structure_id': new_room.id_structure,
                'operation_result': 'success'
            })
            return jsonify(new_room.to_dict()), 201
        except IntegrityError as e:
            db.rollback()
            logger.error("Room creation failed due to integrity constraint", extra={
                'room_name': data.get('name'),
                'room_capacity': data.get('capacity'),
                'structure_id': data.get('id_structure'),
                'error_type': 'integrity_constraint',
                'error_details': str(e),
                'operation_result': 'failed'
            })
            return jsonify({"error": f"Room creation failed due to constraint violation: {str(e)}"}), 400
        except SQLAlchemyError as e:
            db.rollback()
            logger.error("Database error during room creation", extra={
                'room_name': data.get('name'),
                'room_capacity': data.get('capacity'),
                'structure_id': data.get('id_structure'),
                'error_type': 'database_error',
                'error_details': str(e),
                'operation_result': 'failed'
            })
            return jsonify({"error": "Failed to create room due to database error"}), 500
        except (ValueError, TypeError) as e:
            db.rollback()
            logger.exception("Unexpected error during room creation", extra={
                'room_name': data.get('name'),
                'room_capacity': data.get('capacity'),
                'structure_id': data.get('id_structure'),
                'error_type': 'unexpected_error',
                'error_details': str(e),
                'operation_result': 'failed'
            }, exc_info=True)
            return jsonify({"error": "An unexpected error occurred while creating the room"}), 500


# Get all rooms by structure
@room_bp.route("/rooms", methods=["GET"])
@jwt_required()
@log_route(include_request_data=True)
@log_database_operation("READ")
def get_rooms():
    """
    Return a JSON array of rooms for a fixed structure.
    
    Queries the database for Room records with id_structure currently hard-coded to 1, serializes each Room using its to_dict() method, and returns the list as a JSON response. The function does not accept parameters; behavior will need updating when structure selection is implemented via request parameters.
    """
    with get_db() as db:  # Using 'with' to properly manage the db session
        try:
            id_structure = (
                1  # Get structure ID from query params. For now, this value is fixed.
            )

            if id_structure:
                rooms = db.query(Room).filter(Room.id_structure == id_structure).all()
            else:
                rooms = db.query(
                    Room
                ).all()  # Return all rooms if no structure is specified

            room_data = [room.to_dict() for room in rooms]
            logger.info("Rooms retrieved successfully", extra={
                'rooms_count': len(room_data),
                'structure_id': id_structure,
                'operation_result': 'success',
                'room_names': [room['name'] for room in room_data]
            })
            return jsonify(room_data)
        except SQLAlchemyError as e:
            logger.error("Database error retrieving rooms", extra={
                'structure_id': id_structure,
                'error_type': 'database_error',
                'error_details': str(e),
                'operation_result': 'failed'
            })
            return jsonify({"error": "Failed to retrieve rooms due to database error"}), 500
        except (ValueError, TypeError) as e:
            logger.exception("Unexpected error retrieving rooms", extra={
                'structure_id': id_structure,
                'error_type': 'unexpected_error',
                'error_details': str(e),
                'operation_result': 'failed'
            }, exc_info=True)
            return jsonify({"error": "An unexpected error occurred while retrieving rooms"}), 500


# Get room by ID
@room_bp.route("/rooms/<int:room_id>", methods=["GET"])
@jwt_required()
@log_route(include_request_data=True)
@log_database_operation("READ")
def get_room(room_id):
    """
    Retrieve a room by its ID and return its details as JSON.

    Parameters:
        room_id (int): The ID of the room to retrieve.

    Returns:
        Flask response: JSON with room details if found, or an error message with HTTP 404 if not found.
    """
    with get_db() as db:  # Using 'with' statement here as well
        try:
            room = db.query(Room).filter(Room.id == room_id).first()
            if room:
                logger.info("Room retrieved successfully", extra={
                    'room_id': room_id,
                    'room_name': room.name,
                    'room_capacity': room.capacity,
                    'structure_id': room.id_structure,
                    'operation_result': 'success'
                })
                return jsonify(room.to_dict())
            logger.warning("Room not found", extra={
                'room_id': room_id,
                'operation_result': 'not_found'
            })
            return jsonify({"error": "Room not found"}), 404
        except SQLAlchemyError as e:
            logger.error("Database error retrieving room", extra={
                'room_id': room_id,
                'error_type': 'database_error',
                'error_details': str(e),
                'operation_result': 'failed'
            })
            return jsonify({"error": "Failed to retrieve room due to database error"}), 500
        except (ValueError, TypeError) as e:
            logger.exception("Unexpected error retrieving room", extra={
                'room_id': room_id,
                'error_type': 'unexpected_error',
                'error_details': str(e),
                'operation_result': 'failed'
            }, exc_info=True)
            return jsonify({"error": "An unexpected error occurred while retrieving the room"}), 500


# Update a room
@room_bp.route("/rooms/<int:room_id>", methods=["PUT"])
@jwt_required()
@log_route(include_request_data=True, include_response_data=True)
@log_database_operation("UPDATE")
def update_room(room_id):
    """
    Update the details of an existing room by its ID.

    If the room exists, updates its fields based on the provided JSON payload and returns the updated room as JSON. Returns a 404 error if the room is not found, or a 400 error for invalid input values.

    Parameters:
        room_id (int): The ID of the room to update.

    Returns:
        flask.Response: JSON response with the updated room details (HTTP 200), or an error message (HTTP 400 or 404).
    """
    with get_db() as db:
        try:
            room = db.query(Room).filter(Room.id == room_id).first()
            if not room:
                logger.warning("Room not found for update", extra={
                    'room_id': room_id,
                    'operation_result': 'not_found'
                })
                return jsonify({"error": "Room not found"}), 404

            data = request.get_json()
            
            # Log update attempt with details
            logger.info("Attempting room update", extra=safe_extra_fields({
                'room_id': room_id,
                'current_name': room.name,
                'current_capacity': room.capacity,
                'update_fields': list(data.keys()) if data else [],
                'operation': 'update_validation'
            }))
            
            # Validate input data
            validation_error = _validate_room_update_data(data, db)
            if validation_error:
                logger.warning("Room update validation failed", extra={
                    'room_id': room_id,
                    'validation_error': validation_error,
                    'operation_result': 'validation_failed'
                })
                return jsonify({"error": validation_error}), 400

            # Track what fields are being updated
            updated_fields = {}
            if "name" in data:
                updated_fields['name'] = {'old': room.name, 'new': data["name"]}
                room.name = data["name"]
            if "capacity" in data:
                updated_fields['capacity'] = {'old': room.capacity, 'new': data["capacity"]}
                room.capacity = data["capacity"]
            if "id_structure" in data:
                updated_fields['id_structure'] = {'old': room.id_structure, 'new': data["id_structure"]}
                room.id_structure = data["id_structure"]

            db.commit()
            logger.info("Room updated successfully", extra=safe_extra_fields({
                'room_id': room_id,
                'room_name': room.name,
                'updated_fields': updated_fields,
                'operation_result': 'success'
            }))
            return jsonify(room.to_dict()), 200
        except IntegrityError as e:
            db.rollback()
            logger.error("Room update failed due to integrity constraint", extra={
                'room_id': room_id,
                'error_type': 'integrity_constraint',
                'error_details': str(e),
                'operation_result': 'failed'
            })
            return jsonify({"error": f"Room update failed due to constraint violation: {str(e)}"}), 400
        except SQLAlchemyError as e:
            db.rollback()
            logger.error("Database error during room update", extra={
                'room_id': room_id,
                'error_type': 'database_error',
                'error_details': str(e),
                'operation_result': 'failed'
            })
            return jsonify({"error": "Failed to update room due to database error"}), 500
        except (ValueError, TypeError) as e:
            db.rollback()
            logger.exception("Unexpected error during room update", extra={
                'room_id': room_id,
                'error_type': 'unexpected_error',
                'error_details': str(e),
                'operation_result': 'failed'
            }, exc_info=True)
            return jsonify({"error": "An unexpected error occurred while updating the room"}), 500


# Delete a room
@room_bp.route("/rooms/<int:room_id>", methods=["DELETE"])
@jwt_required()
@log_route(include_request_data=True)
@log_database_operation("DELETE")
def delete_room(room_id):
    """
    Delete a room by its ID and return a JSON response indicating the result.

    If the specified room exists, it is removed from the database and a success message is returned with HTTP 200. If not found, returns an error message with HTTP 404.

    Parameters:
        room_id (int): Unique identifier of the room to delete.

    Returns:
        tuple: JSON response and HTTP status code.
    """
    with get_db() as db:  # Again, using 'with' for context management
        room = db.query(Room).filter(Room.id == room_id).first()

        if room:
            # Log deletion attempt with room details
            room_details = {
                'room_id': room_id,
                'room_name': room.name,
                'room_capacity': room.capacity,
                'structure_id': room.id_structure,
                'operation': 'delete_attempt'
            }
            logger.info("Attempting room deletion", extra=room_details)
            
            try:
                db.delete(room)
                db.commit()
                logger.info("Room deleted successfully", extra={
                    **room_details,
                    'operation_result': 'success'
                })
                return jsonify({"message": "Room deleted successfully"}), 200
            except IntegrityError as e:
                db.rollback()
                logger.error("Room deletion failed due to integrity constraints", extra={
                    **room_details,
                    'error_type': 'integrity_constraint',
                    'error_details': str(e),
                    'operation_result': 'failed'
                })
                return jsonify({"error": f"Failed to delete room due to foreign key constraints: {str(e)}"}), 400
            except SQLAlchemyError as e:
                db.rollback()
                logger.error("Database error during room deletion", extra={
                    **room_details,
                    'error_type': 'database_error',
                    'error_details': str(e),
                    'operation_result': 'failed'
                })
                return jsonify({"error": f"Failed to delete room: {str(e)}"}), 500
            except (ValueError, TypeError) as e:
                db.rollback()
                logger.exception("Unexpected error during room deletion", extra={
                    **room_details,
                    'error_type': 'unexpected_error',
                    'error_details': str(e),
                    'operation_result': 'failed'
                }, exc_info=True)
                return jsonify({"error": "An unexpected error occurred while deleting the room"}), 500

        logger.warning("Room not found for deletion", extra={
            'room_id': room_id,
            'operation_result': 'not_found'
        })
        return jsonify({"error": "Room not found"}), 404
