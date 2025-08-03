# routes/reservation_routes.py
# pylint: disable=C0301,E0611,E0401,W0718,

"""
Reservation Routes for handling reservation-related requests in the system.

This module defines the routes and logic for creating and retrieving reservations.
It supports operations such as creating new reservations and listing all reservations.
"""

import calendar
from datetime import datetime
from flask import Blueprint, request, jsonify
from sqlalchemy import  func
from sqlalchemy.sql import extract
from flask_jwt_extended import jwt_required
from models import Reservation, Room, Structure, StructureReservationsView
from database import SessionLocal

# Create a blueprint for reservations
reservation_bp = Blueprint("reservations", __name__, url_prefix="/api/v1")


@reservation_bp.route("/reservations", methods=["POST"])
@jwt_required()
def create_reservation():
    """
    Creates a new reservation using details from the JSON payload of a POST request.
    
    Validates required fields and date formats, locates the specified room, and adds the reservation to the database. Returns the created reservation details with HTTP 201 on success, or an error message with an appropriate status code if validation fails or the room is not found.
    """
    data = request.get_json()

    # Validate required fields
    required_fields = ["reservationNumber", "startDate", "endDate", "roomName"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    session = SessionLocal()

    try:
        # Validate and parse date fields
        start_date = datetime.strptime(data["startDate"], "%Y-%m-%d")
        end_date = datetime.strptime(data["endDate"], "%Y-%m-%d")

        # Find room ID by name
        room = session.query(Room).filter(Room.name == data["roomName"]).first()
        if not room:
            return jsonify({"error": "Room not found"}), 404

        # Create a new reservation entry
        new_reservation = Reservation(
            id_reference=data["reservationNumber"],
            start_date=start_date,
            end_date=end_date,
            name_reference = data["nameReference"],
            id_room=room.id,
        )

        session.add(new_reservation)
        session.flush()  # Generate reservation ID

        # Commit transaction
        session.commit()

        return (
            jsonify(
                {
                    "message": "Reservation created successfully",
                    "reservation": {
                        "id": new_reservation.id,
                        "reservationNumber": new_reservation.id_reference,
                        "startDate": new_reservation.start_date.strftime("%Y-%m-%d"),
                        "endDate": new_reservation.end_date.strftime("%Y-%m-%d"),
                        "roomName": new_reservation.room.to_dict(),
                    },
                }
            ),
            201,
        )

    except ValueError:
        session.rollback()
        return jsonify({"error": "Invalid date format. Use 'YYYY-MM-DD'"}), 400
    except KeyError as e:
        session.rollback()
        return jsonify({"error": f"Missing key: {str(e)}"}), 400
    # pylint: disable=W0718
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@reservation_bp.route("/reservations/<int:reservation_id>", methods=["PATCH"])
@jwt_required()
def update_reservation(reservation_id):
    """
    Update fields of an existing reservation identified by its ID.
    
    Parameters:
        reservation_id (int): Unique identifier of the reservation to update.
    
    Returns:
        flask.Response: JSON response with updated reservation details and HTTP 200 on success, or an error message with appropriate HTTP status code if the reservation or room is not found, or if an error occurs.
    """
    data = request.get_json()

    db = SessionLocal()
    try:
        reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()

        if not reservation:
            return jsonify({"error": f"Reservation with ID {reservation_id} not found"}), 404

        # Optional updates
        if "start_date" in data:
            reservation.start_date = datetime.strptime(
                data["start_date"], "%a, %d %b %Y %H:%M:%S GMT"
            )
        if "end_date" in data:
            reservation.end_date = datetime.strptime(
                data["end_date"], "%a, %d %b %Y %H:%M:%S GMT"
            )
        if "name_reference" in data:
            reservation.name_reference = data["name_reference"]
        if "id_reference" in data:
            reservation.id_reference = data["id_reference"]
        if "status" in data:
            reservation.status = data["status"]
        if "room" in data and isinstance(data["room"], dict) and "id" in data["room"]:
            room = db.query(Room).filter(Room.id == data["room"]["id"]).first()
            if not room:
                return jsonify({"error": "Room not found"}), 404
            reservation.id_room = room.id

        db.commit()

        return jsonify({
            "message": "Reservation updated successfully",
            "reservation": {
                "id": reservation.id,
                "reservationNumber": reservation.id_reference,
                "status": reservation.status,
                "startDate": reservation.start_date.strftime("%Y-%m-%d"),
                "endDate": reservation.end_date.strftime("%Y-%m-%d"),
                "name_reference": reservation.name_reference,
                "roomName": reservation.room.to_dict(),
            }
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Error updating reservation: {str(e)}"}), 500
    finally:
        db.close()
@reservation_bp.route("/reservations/<int:reservation_id>", methods=["DELETE"])
@jwt_required()
def delete_reservation(reservation_id):
    """
    Deletes a reservation identified by its ID.
    
    Returns:
        A JSON response confirming successful deletion with HTTP 200, or an error message with HTTP 404 if not found, or HTTP 500 on failure.
    """
    db = SessionLocal()
    try:
        reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()

        if not reservation:
            return jsonify({"error": f"Reservation with ID {reservation_id} not found"}), 404

        db.delete(reservation)
        db.commit()

        return jsonify({"message": f"Reservation {reservation_id} deleted successfully"}), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Error deleting reservation: {str(e)}"}), 500
    finally:
        db.close()


@reservation_bp.route("/reservations", methods=["GET"])
@jwt_required()
def get_reservations():
    """
    Returns a JSON response with a list of all reservations.
    
    Currently returns an empty list placeholder; intended to be replaced with actual reservation data from the database.
    """
    # This would typically query the database to get reservations
    # Here, you can modify this to use your actual database retrieval logic
    reservations = []  # You may need to query your reservations table here
    return jsonify({"reservations": reservations})


@reservation_bp.route("/reservations/structure/<structure_id>", methods=["GET"])
@jwt_required()
def get_reservations_by_structure(structure_id):
    """
    Retrieve all reservations associated with a given structure ID.
    
    Parameters:
        structure_id (int): Unique identifier of the structure.
    
    Returns:
        flask.Response: JSON array of reservation details, including structure, reservation, and room information.
    """
    db = SessionLocal()
    reservations = (
        db.query(StructureReservationsView)
        .filter(StructureReservationsView.structure_id == structure_id)
        .all()
    )
    db.close()
    return jsonify([{
        "structure_id": r.structure_id,
        "structure_name": r.structure_name,
        "reservation_id": r.reservation_id,
        "id_reference": r.id_reference,
        "start_date": r.start_date.isoformat(),
        "end_date": r.end_date.isoformat(),
        "room_id": r.room_id,
        "status": r.status,
        "name_reference": r.name_reference,
        "room_name": r.room_name
    } for r in reservations])

@reservation_bp.route("/reservations/admin/<int:reservation_id>", methods=["GET"])
@jwt_required()
def get_admin_reservations_by_id(reservation_id):
    """
    Retrieve a reservation by its unique ID.
    
    Returns:
        JSON response with reservation details if found, or a 404 error if the reservation does not exist. Returns a 500 error for unexpected exceptions.
    """
    db = SessionLocal()
    try:
        reservation = (
            db.query(Reservation)
            .filter(Reservation.id == str(reservation_id))
            .first()
        )

        if not reservation:
            return jsonify({"error": f"Reservation with ID {reservation_id} not found"}), 404

        return jsonify(reservation.to_dict())
    except Exception as e:
        return jsonify({"error": f"Error retrieving reservation: {str(e)}"}), 500
    finally:
        db.close()


@reservation_bp.route("/reservations/check/<int:reservation_id>", methods=["GET"])
#@jwt_required() Not needed as this endpoint is for public access
def check_get_reservations_by_id(reservation_id):
    """
    Retrieve a reservation by its unique ID.
    
    Returns:
        JSON response with reservation details if found, or a 404 error if the reservation does not exist. Returns a 500 error for unexpected exceptions.
    """
    db = SessionLocal()
    try:
        reservation = (
            db.query(Reservation)
            .filter(Reservation.id_reference == str(reservation_id))
            .first()
        )

        if not reservation:
            return jsonify({"error": f"Reservation with ID {reservation_id} not found"}), 404

        return jsonify({'id_reference':reservation_id}), 200
    except Exception as e:
        return jsonify({"error": f"Error retrieving reservation: {str(e)}"}), 500
    finally:
        db.close()

@reservation_bp.route("/reservations/monthly/<int:structure_id>", methods=["GET"])
@jwt_required()
def get_reservations_per_month(structure_id):
    """
    Return the number of reservations per month for a given structure.
    
    Parameters:
        structure_id (int): Unique identifier of the structure.
    
    Returns:
        flask.Response: JSON array with each month's name and the corresponding reservation count. Returns 404 if the structure does not exist.
    """
    db = SessionLocal()
    try:
        # Check if the structure exists
        structure = db.query(Structure).filter(Structure.id == structure_id).first()
        if not structure:
            return jsonify({"message": "Structure not found"}), 404


        # Create base months with 0
        months = {i: 0 for i in range(1, 13)}

        # Query reservations grouped by month for the specific structure
        # pylint: disable=E1102
        results = (
            db.query(
                extract("month", Reservation.start_date).label("month"),
                func.count(Reservation.id).label("total_reservations"),
            )
            .join(Room)
            .filter(Room.id_structure == structure_id)
            .group_by(extract("month", Reservation.start_date))
            .all()
        )

        # Update the dictionary with actual values
        for month, total in results:
            months[int(month)] = total

        # Return results with months and their respective reservation count
        return jsonify([
            {"month": calendar.month_name[m], "total_reservations": count}
            for m, count in months.items()
        ]), 200

    finally:
        db.close()


@reservation_bp.route("/reservations/<int:reservation_id>/status", methods=["PUT"])
@jwt_required()
def update_reservation_status(reservation_id):
    """
    Update the status of a reservation by its ID.
    
    Validates the new status against allowed values and updates the reservation if found. Returns the updated reservation details as JSON, or an error message if the status is invalid or the reservation does not exist.
    
    Parameters:
        reservation_id (int): The unique identifier of the reservation to update.
    
    Returns:
        flask.Response: JSON response with updated reservation details and HTTP 200 on success, or an error message with appropriate HTTP status code.
    """
    data = request.get_json()
    allowed_statuses = {"Approved", "Pending", "Declined", "Sent back to customer"}

    if "status" not in data:
        return jsonify({"error": "Missing 'status' field"}), 400

    new_status = data["status"]

    if new_status not in allowed_statuses:
        return jsonify({"error": f"Invalid status. Allowed values: {', '.join(allowed_statuses)}"}), 400

    db = SessionLocal()
    try:
        reservation = db.query(Reservation).filter(Reservation.id == str(reservation_id)).first()

        if not reservation:
            return jsonify({"error": f"Reservation with ID {reservation_id} not found"}), 404

        reservation.status = new_status
        db.commit()

        return jsonify({
            "message": "Reservation status updated successfully",
            "reservation": {
                "id": reservation.id,
                "reservationNumber": reservation.id_reference,
                "status": reservation.status,
                "startDate": reservation.start_date.strftime("%Y-%m-%d"),
                "endDate": reservation.end_date.strftime("%Y-%m-%d"),
                "roomName": reservation.room.to_dict(),
            }
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Error updating reservation status: {str(e)}"}), 500
    finally:
        db.close()
