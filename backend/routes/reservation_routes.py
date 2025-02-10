# routes/reservation_routes.py
# pylint: disable=C0301

"""
Reservation Routes for handling reservation-related requests in the system.

This module defines the routes and logic for creating and retrieving reservations.
It supports operations such as creating new reservations and listing all reservations.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from backend.database import SessionLocal
from ..models import Reservation, Room

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
