# routes/reservation_routes.py
# pylint: disable=C0301,E0611,E0401,W0718,

"""
Reservation Routes for handling reservation-related requests in the system.

This module defines the routes and logic for creating and retrieving reservations.
It supports operations such as creating new reservations and listing all reservations.
"""

import calendar
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import  func
from sqlalchemy.sql import extract
from flask_jwt_extended import get_jwt_identity, jwt_required
from email_handler import EmailService
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

        # Create a new reservation entry
        new_reservation = Reservation(
            id_reference=data["reservationNumber"],
            start_date=start_date,
            end_date=end_date,
            name_reference = data["nameReference"],
            email=data["email"],
            telephone=data.get("telephone", ""),  # Optional field with default empty string
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
            from models import EmailConfig
            from email_handler import EmailService
            from routes.email_config_routes import get_encryption_key
            
            current_user_id = get_jwt_identity()
            email_session = SessionLocal()
            
            try:
                # Get user's email configuration from database
                email_config = email_session.query(EmailConfig).filter(
                    EmailConfig.user_id == current_user_id,
                    EmailConfig.is_active == True
                ).first()
                
                if not email_config:
                    current_app.logger.error("No email configuration found for user")
                    raise Exception("Email configuration not found. Please configure email settings first.")
                
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
            import traceback
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
        if "email" in data:
            reservation.email = data["email"]
        if "telephone" in data:
            reservation.telephone = data["telephone"]
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
    Retrieve all reservations linked to a specific structure.
    
    Parameters:
        structure_id (int): The unique ID of the structure whose reservations are to be retrieved.
    
    Returns:
        flask.Response: A JSON array containing details of each reservation, including structure, reservation, and room information.
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
    Retrieve reservation details by its unique ID for administrative purposes.
    
    Parameters:
        reservation_id (int): The primary key ID of the reservation to retrieve.
    
    Returns:
        Response: JSON object with reservation details and HTTP 200 if found; 404 if not found; 500 on unexpected errors.
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
    Checks for the existence of a reservation by its reference ID and returns the reference if found.
    
    Returns:
        JSON response containing the reservation's reference ID with HTTP 200 if found, 404 if not found, or 500 on error.
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
    Returns the count of reservations for each month for a specified structure.
    
    Parameters:
        structure_id (int): The unique identifier of the structure to query.
    
    Returns:
        flask.Response: A JSON array where each element contains the month's name and the total number of reservations for that month. Returns a 404 response if the structure does not exist.
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
