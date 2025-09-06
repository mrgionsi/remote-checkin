# pylint: disable=C0301,E0611,E0401,W0718,E0611,R0912,R0915,R1702,W0718,R0914,R0911,W0107

"""
Reservation Routes for handling reservation-related requests in the system.

This module defines the routes and logic for creating and retrieving reservations.
It supports operations such as creating new reservations and listing all reservations.
"""

import calendar
import traceback
from datetime import datetime

from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import  func
from sqlalchemy.sql import extract
from flask_jwt_extended import get_jwt_identity, jwt_required

from models import Reservation, Room, Structure, StructureReservationsView, EmailConfig,Client, ClientReservations
from email_handler import EmailService
from routes.email_config_routes import get_encryption_key
from utils.email_utils import get_admin_email_config
from database import SessionLocal


class EmailConfigurationError(Exception):
    """Custom exception for email configuration errors."""
    pass

# Create a blueprint for reservations
reservation_bp = Blueprint("reservations", __name__, url_prefix="/api/v1")


@reservation_bp.route("/reservations", methods=["POST"])
@jwt_required()
def create_reservation():
    """
    Create a new reservation from JSON payload, persist it to the database, and (optionally) send a confirmation email.
    
    Expects a POST JSON body with the required fields:
      - reservationNumber (str): external reservation identifier
      - startDate (str): reservation start in YYYY-MM-DD
      - endDate (str): reservation end in YYYY-MM-DD
      - roomName (str): exact room name to look up
      - email (str): guest email address
    Optional fields:
      - nameReference (str)
      - telephone (str)
      - numberOfPeople (int): number of people for this reservation (default: 1, max: room capacity)
    
    Behavior:
      - Validates required fields and parses dates (format YYYY-MM-DD).
      - Looks up Room by name and returns 404 if not found.
      - Creates and commits a Reservation record (returns 201 on success).
      - After committing, attempts to send a confirmation email using the caller's active EmailConfig; email failures are logged and do not roll back the reservation.
    
    Responses:
      - 201: JSON payload with created reservation details.
      - 400: missing fields or invalid date formats.
      - 404: room not found.
      - 500: unexpected server error.
    """
    data = request.get_json()

    # Validate required fields
    required_fields = ["reservationNumber", "startDate", "endDate", "roomName", "email"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    session = SessionLocal()

    try:
        # Debug: Log the received data
        current_app.logger.info(f"Received reservation data: {data}")
        current_app.logger.info(f"startDate type: {type(data['startDate'])}, value: {data['startDate']}")
        current_app.logger.info(f"endDate type: {type(data['endDate'])}, value: {data['endDate']}")

        # Validate and parse date fields
        try:
            start_date = datetime.strptime(data["startDate"], "%Y-%m-%d")
            end_date = datetime.strptime(data["endDate"], "%Y-%m-%d")
        except ValueError as e:
            current_app.logger.error(f"Date parsing error: {e}")
            current_app.logger.error(f"startDate: '{data['startDate']}', endDate: '{data['endDate']}'")
            return jsonify({"error": f"Invalid date format. Expected YYYY-MM-DD, got startDate: '{data['startDate']}', endDate: '{data['endDate']}'"}), 400

        # Find room ID by name
        room = session.query(Room).filter(Room.name == data["roomName"]).first()
        if not room:
            return jsonify({"error": "Room not found"}), 404

        # Validate number_of_people if provided - safely coerce to int
        raw_number_of_people = data.get("numberOfPeople", 1)
        try:
            number_of_people = int(raw_number_of_people)
        except (ValueError, TypeError):
            return jsonify({"error": f"Invalid number of people: '{raw_number_of_people}'. Must be a valid integer."}), 400
        
        if number_of_people < 1:
            return jsonify({"error": "Number of people must be at least 1"}), 400
        if number_of_people > room.capacity:
            return jsonify({"error": f"Number of people ({number_of_people}) cannot exceed room capacity ({room.capacity})"}), 400

        # Create a new reservation entry
        new_reservation = Reservation(
            id_reference=data["reservationNumber"],
            start_date=start_date,
            end_date=end_date,
            name_reference = data.get("nameReference"),
            email=data["email"],
            telephone=data.get("telephone", ""),  # Optional field with default empty string
            number_of_people=number_of_people,
            id_room=room.id,
        )

        session.add(new_reservation)
        session.flush()  # Generate reservation ID

        # Commit transaction
        session.commit()

        # Capture reservation data before session is closed
        reservation_number = new_reservation.id_reference
        room_name = room.name

        # Close the first session
        session.close()

        # Send email after committing reservation
        try:
            # Get user's email configuration from database

            current_user_id = get_jwt_identity()
            email_session = SessionLocal()

            try:
                # Get user's email configuration from database
                email_config = email_session.query(EmailConfig).filter(
                    EmailConfig.user_id == current_user_id,
                                            EmailConfig.is_active.is_(True)
                ).first()

                if not email_config:
                    current_app.logger.error("No email configuration found for user")
                    raise EmailConfigurationError("Email configuration not found. Please configure email settings first.")

                # Use database configuration
                current_app.logger.info("Using database email configuration")
                encryption_key = get_encryption_key()
                email_service = EmailService(config=email_config, encryption_key=encryption_key)

            finally:
                email_session.close()

            # Prepare reservation data for email
            reservation_data = {
                'reservation_number': reservation_number,
                'guest_name': data.get('nameReference', 'Guest'),
                'start_date': data['startDate'],
                'end_date': data['endDate'],
                'room_name': room_name
            }

            # Log the data being sent
            current_app.logger.info(f"Preparing to send email to: {data['email']}")
            current_app.logger.info(f"Reservation data: {reservation_data}")
            current_app.logger.info(f"Email service type: {type(email_service)}")
            # current_app.logger.info(f"Mail instance type: {type(mail)}")  # Removed as mail is not used in new email system

            # Send confirmation email
            email_result = email_service.send_reservation_confirmation(
                client_email=data["email"],  # Use email from frontend
                reservation_data=reservation_data
            )

            # Log email result
            if email_result['status'] == 'error':
                current_app.logger.warning(f"Failed to send email: {email_result['message']}")
                current_app.logger.warning(f"Email error type: {email_result.get('error_type', 'unknown')}")
            else:
                current_app.logger.info("Reservation confirmation email sent successfully")
                current_app.logger.info(f"Email sent to: {email_result.get('to', 'unknown')}")

        except Exception as e:
            # Log email error but don't fail the reservation creation
            current_app.logger.error(f"Error sending email: {str(e)}")
            current_app.logger.error(f"Email error traceback: {traceback.format_exc()}")

        return (
            jsonify(
                {
                    "message": "Reservation created successfully",
                    "reservation": {
                        "id": new_reservation.id,
                        "reservationNumber": new_reservation.id_reference,
                        "startDate": new_reservation.start_date.strftime("%Y-%m-%d"),
                        "endDate": new_reservation.end_date.strftime("%Y-%m-%d"),
                        "nameReference": new_reservation.name_reference,
                        "email": new_reservation.email,
                        "telephone": new_reservation.telephone,
                        "numberOfPeople": new_reservation.number_of_people,
                        "roomName": room.to_dict(),
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
    Update an existing reservation's fields by its database ID.
    
    Accepts a JSON payload with any of the updatable fields listed below and persists changes to the database.
    
    Payload fields (all optional except at least one meaningful field):
    - start_date, end_date: strings parsed with format "%a, %d %b %Y %H:%M:%S GMT".
    - name_reference (str)
    - id_reference (str)
    - email (str)
    - telephone (str)
    - status (str)
    - number_of_people (int): number of people for this reservation (max: room capacity)
    - room: object containing "id" (int) — if provided, the referenced Room must exist.
    
    Behavior:
    - Commits changes and returns the updated reservation representation on success.
    - Returns 404 if the reservation or referenced room is not found.
    - Returns 500 on unexpected errors.
    
    Returns:
    - Flask JSON response with HTTP 200 and the updated reservation on success; otherwise a JSON error with the appropriate HTTP status code.
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
        if "email" in data:
            reservation.email = data["email"]
        if "telephone" in data:
            reservation.telephone = data["telephone"]
        if "status" in data:
            reservation.status = data["status"]
        if "number_of_people" in data:
            number_of_people = data["number_of_people"]
            if number_of_people < 1:
                return jsonify({"error": "Number of people must be at least 1"}), 400
            # Get current room to check capacity
            current_room = db.query(Room).filter(Room.id == reservation.id_room).first()
            if number_of_people > current_room.capacity:
                return jsonify({"error": f"Number of people ({number_of_people}) cannot exceed room capacity ({current_room.capacity})"}), 400
            reservation.number_of_people = number_of_people
        if "room" in data and isinstance(data["room"], dict) and "id" in data["room"]:
            room = db.query(Room).filter(Room.id == data["room"]["id"]).first()
            if not room:
                return jsonify({"error": "Room not found"}), 404
            # If changing room, validate number_of_people against new room capacity
            if reservation.number_of_people > room.capacity:
                return jsonify({"error": f"Current number of people ({reservation.number_of_people}) cannot exceed new room capacity ({room.capacity})"}), 400
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
                "numberOfPeople": reservation.number_of_people,
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
    Delete a reservation by its database ID.
    
    Parameters:
        reservation_id (int): Primary key of the reservation to remove.
    
    Returns:
        A Flask JSON response with:
          - 200 and a success message when the reservation is deleted,
          - 404 if no reservation with the given ID exists,
          - 500 on unexpected errors.
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
    Return a JSON response containing a list of reservations.
    
    This endpoint responds with {"reservations": [...]}. Currently the list is a placeholder (empty) and should be replaced with actual reservation objects retrieved from the database. Requires authenticated access (JWT) in the application routes.
    """
    # This would typically query the database to get reservations
    # Here, you can modify this to use your actual database retrieval logic
    reservations = []  # You may need to query your reservations table here
    return jsonify({"reservations": reservations})


@reservation_bp.route("/reservations/structure/<structure_id>", methods=["GET"])
@jwt_required()
def get_reservations_by_structure(structure_id):
    """
    Return all reservations for the specified structure as a JSON array.
    
    Queries the read-only StructureReservationsView for reservations whose room belongs to the given structure. Each reservation in the response includes structure and room identifiers, reference id, ISO-8601 formatted start and end dates, status, and guest name.
    
    Parameters:
        structure_id (int): ID of the Structure to fetch reservations for.
    
    Returns:
        flask.Response: JSON array of reservation objects. If no reservations exist for the structure, an empty list is returned.
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
    Retrieve a reservation by its ID for administrative use.
    
    Looks up the Reservation by primary key (accepts int or string-like IDs) and returns its serialized representation as JSON.
    
    Parameters:
        reservation_id (int | str): Reservation primary key. The value is compared as a string against the stored Reservation.id.
    
    Returns:
        Flask Response: JSON body with the reservation dictionary and HTTP 200 when found; JSON error with HTTP 404 if not found; JSON error with HTTP 500 on unexpected failures.
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


@reservation_bp.route("/reservations/check/<string:reservation_id>", methods=["GET"])
#@jwt_required() Not needed as this endpoint is for public access
def check_get_reservations_by_id(reservation_id):
    """
    Check whether a reservation exists by its reference ID and return the reference when found.
    Also returns capacity information needed for client registration.
    
    Parameters:
        reservation_id (str): The reservation reference (id_reference) to look up.
    
    Returns:
        Flask Response: JSON with reservation details including capacity info and HTTP 200 if found;
        JSON error and HTTP 404 if not found; JSON error and HTTP 500 on unexpected errors.
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

        # Get count of clients linked to the reservation
        client_count = (
            db.query(Client)
            .join(ClientReservations, Client.id == ClientReservations.id_client)
            .filter(ClientReservations.id_reservation == reservation.id)
            .count()
        )

        return jsonify({
            'id': reservation.id,
            'id_reference': reservation_id,
            'number_of_people': reservation.number_of_people or 1,
            'status': reservation.status,
            'registered_clients_count': client_count
        }), 200
    except Exception as e:
        return jsonify({"error": f"Error retrieving reservation: {str(e)}"}), 500
    finally:
        db.close()

@reservation_bp.route("/reservations/monthly/<int:structure_id>", methods=["GET"])
@jwt_required()
def get_reservations_per_month(structure_id):
    """
    Return the number of reservations per calendar month for a given structure.
    
    Returns a list of 12 entries (January–December) with counts for each month; months with no reservations are returned with a count of 0.
    
    Parameters:
        structure_id (int): ID of the structure to query.
    
    Returns:
        flask.Response: JSON array of objects {"month": "<Month Name>", "total_reservations": <int>} and HTTP status 200.
        If the specified structure does not exist, returns a 404 JSON response {"message": "Structure not found"}.
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
    Update a reservation's status and notify the structure admin's configured email when appropriate.
    
    Updates the Reservation identified by reservation_id to the provided status (one of "Approved", "Pending", "Declined", "Sent back to customer"). If the status changes to "Approved" or "Sent back to customer", the function attempts to send a notification email to the reservation's email using the structure admin's active EmailConfig; email failures are logged and do not prevent the status update. The function returns a JSON response with the updated reservation data on success or an error message with an appropriate HTTP status code on failure.
    
    Parameters:
        reservation_id: The reservation identifier (int or str). The value is compared against Reservation.id.
    
    Returns:
        A Flask JSON response:
          - 200 with the updated reservation object on success.
          - 400 if the request payload is missing or contains an invalid status.
          - 404 if no reservation is found with the given ID.
          - 500 for server-side errors.
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

        # Fetch room separately to avoid lazy loading issues
        room = db.query(Room).filter(Room.id == reservation.id_room).first()

        old_status = reservation.status
        reservation.status = new_status
        db.commit()

        # Send email notification if status changed to "Approved" or "Sent back to customer"
        if old_status != new_status and new_status in ["Approved", "Sent back to customer"]:
            try:
                # Get admin email configuration
                email_config, _ = get_admin_email_config(reservation)

                if email_config and reservation.email:
                    encryption_key = get_encryption_key()
                    email_service = EmailService(config=email_config, encryption_key=encryption_key)

                    email_result = None
                    # Prepare email data based on status
                    if new_status == "Approved":
                        email_result = email_service.send_reservation_approval_notification(
                            reservation.email,
                            {
                                'reservation_number': reservation.id_reference,
                                'guest_name': reservation.name_reference,
                                'start_date': reservation.start_date.strftime('%Y-%m-%d') if reservation.start_date else 'N/A',
                                'end_date': reservation.end_date.strftime('%Y-%m-%d') if reservation.end_date else 'N/A',
                                'room_name': reservation.room.name if reservation.room else 'N/A'
                            }
                        )
                    elif new_status == "Sent back to customer":
                        email_result = email_service.send_reservation_revision_notification(
                            reservation.email,
                            {
                                'reservation_number': reservation.id_reference,
                                'guest_name': reservation.name_reference,
                                'start_date': reservation.start_date.strftime('%Y-%m-%d') if reservation.start_date else 'N/A',
                                'end_date': reservation.end_date.strftime('%Y-%m-%d') if reservation.end_date else 'N/A',
                                'room_name': reservation.room.name if reservation.room else 'N/A'
                            }
                        )

                    if email_result and email_result.get('status') == 'success':
                        current_app.logger.info(f"Status change notification sent successfully to {reservation.email}")
                    elif email_result:
                        current_app.logger.warning(f"Failed to send status change notification: {email_result.get('message', 'Unknown error')}")
                else:
                    current_app.logger.warning(f"No email configuration found for admin or no client email for reservation {reservation.id}")

            except Exception as e:
                current_app.logger.error(f"Error sending status change notification: {str(e)}")
                current_app.logger.error(f"Traceback: {traceback.format_exc()}")

        return jsonify({
            "message": "Reservation status updated successfully",
            "reservation": {
                "id": reservation.id,
                "reservationNumber": reservation.id_reference,
                "status": reservation.status,
                "startDate": reservation.start_date.strftime("%Y-%m-%d"),
                "endDate": reservation.end_date.strftime("%Y-%m-%d"),
                "roomName": room.to_dict() if room else {},
            }
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Error updating reservation status: {str(e)}"}), 500
    finally:
        db.close()
