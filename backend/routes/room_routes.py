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

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

#pylint: disable=E0611,E0401
from models import Room, Structure
from app_logging.config import get_logger
from app_logging.decorators import log_route, log_database_operation, log_function
from app_logging.utils import safe_extra_fields
from utils.authz import is_superadmin
from utils.route_helpers import (
    get_user_structure_ids,
    error_response,
    get_current_user_id,
    require_structure_access,
)
from database import get_db  # Use absolute import

# Configure logging
logger = get_logger(__name__)

room_bp = Blueprint("room", __name__, url_prefix="/api/v1")


@log_function(include_args=True, include_result=True, max_arg_length=200)
def _validate_room_update_data(data, db):
    """Validate room update data and return error message if invalid."""
    error = None
    if "name" in data and not data["name"].strip():
        error = "Room name cannot be empty"
    if error is None and "capacity" in data:
        try:
            capacity = int(data["capacity"])
            if capacity <= 0:
                error = "Capacity must be a positive number"
        except ValueError:
            error = "Invalid capacity value"
    if error is None and "id_structure" in data:
        try:
            structure = db.query(Structure).filter(Structure.id == data["id_structure"]).first()
            if not structure:
                error = "Invalid structure ID"
        except SQLAlchemyError as e:
            logger.error("Database error validating structure ID %s: %s", data["id_structure"], str(e))
            error = "Failed to validate structure ID due to database error"
    if error is None and "is_active" in data and not isinstance(data["is_active"], bool):
        error = "Invalid active status value"
    return error


# Add a new room
@room_bp.route("/rooms", methods=["POST"])
@jwt_required()
@log_route(include_request_data=True)
@log_database_operation("CREATE")
def add_room():  # pylint: disable=R0911
    """
    Creates a new room using JSON data from the request and adds it to the database.

    Validates that "name", "id_structure", and "capacity" are present in the request body. Returns a JSON error message with status 400 if any required field is missing. On success, returns the created room as JSON with status 201.

    Returns:
        tuple: JSON response containing the new room or an error message, and the corresponding HTTP status code.
    """
    with get_db() as db:  # Using the 'with' statement to manage the database session
        data = request.get_json() or {}
        current_user_id, user_error = get_current_user_id()
        if user_error:
            return user_error

        # Validate the input data
        if (
            not data.get("name")
            or not data.get("id_structure")
            or not data.get("capacity")
        ):
            return error_response("Missing required fields: 'name', 'capacity', or 'id_structure'", 400)
        _, structure_error = require_structure_access(db, data["id_structure"], user_id=current_user_id)
        if structure_error:
            return structure_error
        structure = db.query(Structure).filter(Structure.id == data["id_structure"]).first()
        if not structure:
            return error_response("Invalid structure ID", 400)

        # Create a new room
        new_room = Room(
            name=data["name"],
            capacity=data["capacity"],
            id_structure=data["id_structure"],
            is_active=data.get("is_active", True),
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
            return error_response("Room creation failed due to constraint violation.", 400)
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
            return error_response("Failed to create room due to database error", 500)
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
            return error_response("An unexpected error occurred while creating the room", 500)


# Get all rooms by structure
@room_bp.route("/rooms", methods=["GET"])
@jwt_required()
@log_route(include_request_data=True)
@log_database_operation("READ")
def get_rooms():  # pylint: disable=too-many-return-statements
    """
    Return a JSON array of rooms, optionally filtered by structure_id.

    Queries the database for Room records, optionally filtering by the provided
    ?structure_id query parameter, serializes each Room using its to_dict() method,
    and returns the list as a JSON response.
    """
    with get_db() as db:  # Using 'with' to properly manage the db session
        try:
            current_user_id, user_error = get_current_user_id()
            if user_error:
                return user_error
            raw_structure_id = request.args.get("structure_id")
            id_structure = None
            if raw_structure_id is not None:
                try:
                    id_structure = int(raw_structure_id)
                except (TypeError, ValueError):
                    return error_response("Invalid structure_id. Must be an integer.", 400)

            if id_structure is not None:
                _, structure_error = require_structure_access(db, id_structure, user_id=current_user_id)
                if structure_error:
                    return structure_error
                rooms = db.query(Room).filter(Room.id_structure == id_structure).order_by(Room.id).all()
            else:
                if is_superadmin():
                    rooms = db.query(Room).order_by(Room.id).all()
                else:
                    allowed_structure_ids = get_user_structure_ids(db, current_user_id)
                    if not allowed_structure_ids:
                        return jsonify([])
                    rooms = (
                        db.query(Room)
                        .filter(Room.id_structure.in_(allowed_structure_ids))
                        .order_by(Room.id)
                        .all()
                    )

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
            return error_response("Failed to retrieve rooms due to database error", 500)
        except (ValueError, TypeError) as e:
            logger.exception("Unexpected error retrieving rooms", extra={
                'structure_id': id_structure,
                'error_type': 'unexpected_error',
                'error_details': str(e),
                'operation_result': 'failed'
            }, exc_info=True)
            return error_response("An unexpected error occurred while retrieving rooms", 500)


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
            current_user_id, user_error = get_current_user_id()
            if user_error:
                return user_error
            room = db.query(Room).filter(Room.id == room_id).first()
            if room:
                _, structure_error = require_structure_access(db, room.id_structure, user_id=current_user_id)
                if structure_error:
                    return structure_error
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
            return error_response("Room not found", 404)
        except SQLAlchemyError as e:
            logger.error("Database error retrieving room", extra={
                'room_id': room_id,
                'error_type': 'database_error',
                'error_details': str(e),
                'operation_result': 'failed'
            })
            return error_response("Failed to retrieve room due to database error", 500)
        except (ValueError, TypeError) as e:
            logger.exception("Unexpected error retrieving room", extra={
                'room_id': room_id,
                'error_type': 'unexpected_error',
                'error_details': str(e),
                'operation_result': 'failed'
            }, exc_info=True)
            return error_response("An unexpected error occurred while retrieving the room", 500)


# Update a room
@room_bp.route("/rooms/<int:room_id>", methods=["PUT"])
@jwt_required()
@log_route(include_request_data=True, include_response_data=True)
@log_database_operation("UPDATE")
# pylint: disable=R0911
def update_room(room_id):  # pylint: disable=too-many-branches
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
            current_user_id, user_error = get_current_user_id()
            if user_error:
                return user_error
            room = db.query(Room).filter(Room.id == room_id).first()
            if not room:
                logger.warning("Room not found for update", extra={
                    'room_id': room_id,
                    'operation_result': 'not_found'
                })
                return error_response("Room not found", 404)
            _, structure_error = require_structure_access(db, room.id_structure, user_id=current_user_id)
            if structure_error:
                return structure_error

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
                return error_response(validation_error, 400)
            if "id_structure" in data and not is_superadmin():
                _, structure_error = require_structure_access(db, data["id_structure"], user_id=current_user_id)
                if structure_error:
                    return structure_error

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
            if "is_active" in data:
                updated_fields['is_active'] = {'old': room.is_active, 'new': data["is_active"]}
                room.is_active = data["is_active"]

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
            return error_response("Room update failed due to constraint violation.", 400)
        except SQLAlchemyError as e:
            db.rollback()
            logger.error("Database error during room update", extra={
                'room_id': room_id,
                'error_type': 'database_error',
                'error_details': str(e),
                'operation_result': 'failed'
            })
            return error_response("Failed to update room due to database error", 500)
        except (ValueError, TypeError) as e:
            db.rollback()
            logger.exception("Unexpected error during room update", extra={
                'room_id': room_id,
                'error_type': 'unexpected_error',
                'error_details': str(e),
                'operation_result': 'failed'
            }, exc_info=True)
            return error_response("An unexpected error occurred while updating the room", 500)


# Delete a room
@room_bp.route("/rooms/<int:room_id>", methods=["DELETE"])
@jwt_required()
@log_route(include_request_data=True)
@log_database_operation("DELETE")
def delete_room(room_id):  # pylint: disable=too-many-return-statements
    """
    Delete a room by its ID and return a JSON response indicating the result.

    If the specified room exists, it is removed from the database and a success message is returned with HTTP 200. If not found, returns an error message with HTTP 404.

    Parameters:
        room_id (int): Unique identifier of the room to delete.

    Returns:
        tuple: JSON response and HTTP status code.
    """
    with get_db() as db:  # Again, using 'with' for context management
        try:
            current_user_id, user_error = get_current_user_id()
            if user_error:
                return user_error
            room = db.query(Room).filter(Room.id == room_id).first()

            if not room:
                logger.warning("Room not found for deletion", extra={
                    'room_id': room_id,
                    'operation_result': 'not_found'
                })
                return error_response("Room not found", 404)

            _, structure_error = require_structure_access(db, room.id_structure, user_id=current_user_id)
            if structure_error:
                return structure_error

            # Log deletion attempt with room details
            room_details = {
                'room_id': room_id,
                'room_name': room.name,
                'room_capacity': room.capacity,
                'structure_id': room.id_structure,
                'operation': 'delete_attempt'
            }
            logger.info("Attempting room deletion", extra=room_details)

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
                'room_id': room_id,
                'error_type': 'integrity_constraint',
                'error_details': str(e),
                'operation_result': 'failed'
            })
            return error_response("Failed to delete room due to foreign key constraints.", 400)
        except SQLAlchemyError as e:
            db.rollback()
            logger.error("Database error during room deletion", extra={
                'room_id': room_id,
                'error_type': 'database_error',
                'error_details': str(e),
                'operation_result': 'failed'
            })
            return error_response("Failed to delete room due to database error.", 500)
        except (ValueError, TypeError) as e:
            db.rollback()
            logger.exception("Unexpected error during room deletion", extra={
                'room_id': room_id,
                'error_type': 'unexpected_error',
                'error_details': str(e),
                'operation_result': 'failed'
            }, exc_info=True)
            return error_response("An unexpected error occurred while deleting the room", 500)
