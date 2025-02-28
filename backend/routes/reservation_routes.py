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
from models import Reservation, Room, Structure, StructureReservationsView

from database import SessionLocal

# Create a blueprint for reservations
reservation_bp = Blueprint("reservations", __name__, url_prefix="/api/v1")


@reservation_bp.route("/reservations", methods=["POST"])
def create_reservation():
    """
    Create a new reservation from the JSON payload of a POST request.

    This function extracts reservation details from the incoming JSON payload, validates the presence of
    required fields ("reservationNumber", "startDate", "endDate", "roomName"), and parses the date strings
    into datetime objects. It then queries the database to locate the room by its name. If the room is found,
    a new reservation is created and added to the database. The function commits the transaction and returns
    a JSON response with the reservation details and a 201 status code. If any validation fails (e.g., missing
    fields, invalid date formats) or if the room cannot be found, an appropriate error message with a relevant
    HTTP status code (400, 404, or 500) is returned. The function ensures that the database session is properly
    closed after the operation, rolling back the transaction in case of errors.
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


@reservation_bp.route("/reservations", methods=["GET"])
def get_reservations():
    """
    Return a JSON response containing the global reservations list.

    This function returns the global reservations list wrapped in a JSON response. The reservations are
    returned under the key "reservations".

    Returns:
        flask.Response: A JSON response object containing the global reservations list.
    """
    # This would typically query the database to get reservations
    # Here, you can modify this to use your actual database retrieval logic
    reservations = []  # You may need to query your reservations table here
    return jsonify({"reservations": reservations})


@reservation_bp.route("/reservations/structure/<structure_id>", methods=["GET"])
def get_reservations_by_structure(structure_id):
    """
    Get all reservations for a specific structure.

    Args:
        structure_id (int): The ID of the structure to get reservations for.

    Returns:
        flask.Response: JSON array containing reservation details.
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



@reservation_bp.route("/reservations/<int:reservation_id>", methods=["GET"])
def get_reservations_by_id(reservation_id):
    """
    Get specific reservation

    Args:
        reservation_id (int): The ID of the reservation.

    Returns:
        flask.Response: JSON containing reservation details or a 404 error if not found.
    """
    db = SessionLocal()
    try:
        reservation = (
            db.query(Reservation)
            .filter(Reservation.id == reservation_id)
            .first()
        )

        if not reservation:
            return jsonify({"error": f"Reservation with ID {reservation_id} not found"}), 404

        return jsonify(reservation.to_dict())
    except Exception as e:
        return jsonify({"error": f"Error retrieving reservation: {str(e)}"}), 500
    finally:
        db.close()

@reservation_bp.route("/reservations/monthly/<int:structure_id>", methods=["GET"])
def get_reservations_per_month(structure_id):
    """
    Get monthly reservation counts for a specific structure.

    Args:
        structure_id (int): The ID of the structure to get reservation counts for.

    Returns:
        flask.Response: List of dictionaries containing month names and reservation counts, or an empty array if no reservations or structure doesn't exist.
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
