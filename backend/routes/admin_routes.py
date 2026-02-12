# pylint: disable=C0301,E0611,E0401,W0718,R0801

"""Admin routes module for user authentication, account creation, and profile retrieval.

This module defines Flask routes related to administrative user actions. It includes:
- Authentication endpoint for admin users with JWT token issuance.
- Endpoint for creating new admin users with role assignments.
- Endpoint for retrieving the currently authenticated admin user's profile and associated structures.

All routes are registered under the '/api/v1/admin' URL prefix and require appropriate user roles
(e.g., admin, superadmin) for access.
"""

from datetime import timedelta,datetime,timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from models import User, Reservation, Client, ClientReservations
from services.portale_alloggi_service import PortaleAlloggiService
from utils.encryption_utils import encrypt_password, decrypt_password
from utils.authz import verify_admin_access
from utils.route_helpers import handle_database_error, handle_integrity_error, get_user_structures_query, create_user_response_data
from app_logging.config import get_logger
from app_logging.decorators import log_route, log_database_operation, log_performance
from app_logging.utils import safe_extra_fields
from database import SessionLocal


# Blueprint setup
admin_bp = Blueprint("admin", __name__, url_prefix="/api/v1")

# Configure logging
logger = get_logger(__name__)

# Error messages
USER_NOT_FOUND = "User not found"
INTERNAL_SERVER_ERROR = "Internal server error"
PORTALE_CREDENTIALS_NOT_CONFIGURED = "Portale Alloggi credentials not configured"
RESERVATION_NOT_FOUND = "Reservation not found"
USER_CREATION_OPERATION = "user creation"


def _is_valid_password(password: str) -> bool:
    """
    Validate basic password strength.

    Rules:
    - at least 8 characters
    - at least one letter
    - at least one digit
    """
    if len(password) < 8:
        return False
    has_letter = any(char.isalpha() for char in password)
    has_digit = any(char.isdigit() for char in password)
    return has_letter and has_digit


@admin_bp.route("/admin/login", methods=["POST"])
@log_route(include_request_data=False, include_response_data=True)
def admin_login():
    """
    Authenticate an admin user and return a JWT access token with the user's profile and associated structures.

    Expects a JSON body with `username` and `password`. On success returns HTTP 200 with a JSON object containing:
    - `access_token`: JWT (expires in 2 hours) whose identity is the user ID and includes `username` and `role` claims.
    - `user`: object with `id`, `username`, `name`, `surname`, `email`, `telephone`, `structures` (list of {id, name}), and `role`.

    Possible responses:
    - 200: Authentication successful.
    - 400: Missing `username` or `password`.
    - 401: Invalid credentials.
    - 403: Authenticated user does not have an admin role.
    - 500: Server error.
    """
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username e password sono obbligatori"}), 400

    db_session = SessionLocal()
    try:
        user = db_session.query(User).filter_by(username=username).first()
        if not user:
            return jsonify({"error": "Credenziali non valide"}), 401

        if not check_password_hash(user.password, password):
            return jsonify({"error": "Credenziali non valide"}), 401

        if not user.role or user.role.name.lower() not in ["admin", "superadmin", "administrator"]:
            return jsonify({"error": "Non autorizzato"}), 403

        # JOIN tra AdminStructure e Structure per ottenere id e nome struttura
        structures_query = get_user_structures_query(db_session, user.id)
        structures = structures_query.all()
        # Array di dizionari con id e name
        structures_list = [{"id": s.id_structure, "name": s.name} for s in structures]

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                "username": user.username,
                "role": user.role.name
            },
            expires_delta=timedelta(hours=2)
        )

        return jsonify({
            "access_token": access_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "name": user.name,
                "surname": user.surname,
                "email": user.email,
                "telephone": user.telephone,
                "structures": structures_list,
                "role": user.role.name
            }
        }), 200

    except Exception as e:
        logger.exception("Login error occurred", extra=safe_extra_fields({
            'username': data.get('username'),
            'error_type': type(e).__name__,
            'operation_result': 'failed'
        }))
        return jsonify({"error": "Errore durante il login"}), 500
    finally:
        db_session.close()

#pylint: disable=W0703,R0911
@admin_bp.route("/admin/create", methods=["POST"])
@jwt_required()
@log_route(include_request_data=True)
@log_database_operation("CREATE")
def create_admin_user():
    """
    Create a new admin user from a JSON request.

    Requires JWT authentication and admin role. Expects a JSON body with required fields: `username`, `password`, and `id_role`; optional fields: `name`, `surname`, `email`, and `telephone`. On success inserts a new User record (password is stored hashed) and returns HTTP 201 with the created user's data (id, username, name, surname, email, telephone, id_role). Returns HTTP 400 when required fields are missing or the username already exists, HTTP 401 for missing/invalid JWT, HTTP 403 for insufficient permissions, and HTTP 500 for unexpected server errors.
    """
    # Verify JWT authentication and admin role
    error_response, error_code = verify_admin_access()
    if error_response:
        return error_response, error_code

    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    name = data.get("name")
    surname = data.get("surname")
    email = data.get("email")
    telephone = data.get("telephone")
    id_role = data.get("id_role")

    if not username or not password or not id_role:
        return jsonify({"error": "username, password and id_role are required"}), 400

    db_session = SessionLocal()
    try:
        if db_session.query(User).filter_by(username=username).first():
            return jsonify({"error": "Username already exists"}), 400

        hashed_password = generate_password_hash(password)

        new_user = User(
            username=username,
            password=hashed_password,
            name=name,
            surname=surname,
            email=email,
            telephone=telephone,
            id_role=id_role
        )
        db_session.add(new_user)
        db_session.commit()

        return jsonify(create_user_response_data(new_user, new_user.role)), 201
#pylint: disable=W0703,R0911
    except IntegrityError as e:
        db_session.rollback()
        return handle_integrity_error(e, USER_CREATION_OPERATION, username=data.get('username'), email=data.get('email'))
    except SQLAlchemyError:
        db_session.rollback()
        return handle_database_error(Exception("Database error"), USER_CREATION_OPERATION, username=data.get('username'))
    except Exception:
        db_session.rollback()
        return handle_database_error(Exception("Unexpected error"), USER_CREATION_OPERATION, username=data.get('username'))
    finally:
        db_session.close()


@admin_bp.route("/admin/change-password", methods=["POST"])
@jwt_required()
@log_route(include_request_data=False)
@log_database_operation("UPDATE")
def change_admin_password():
    """
    Change password for the currently authenticated admin user.

    Expects JSON body with:
    - current_password
    - new_password
    - confirm_password
    """
    error_resp, error_code = verify_admin_access()
    if error_resp:
        return error_resp, error_code

    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON data required"}), 400

    current_password = str(data.get("current_password", "")).strip()
    new_password = str(data.get("new_password", "")).strip()
    confirm_password = str(data.get("confirm_password", "")).strip()

    if not current_password or not new_password or not confirm_password:
        return jsonify({"error": "current_password, new_password and confirm_password are required"}), 400

    if new_password != confirm_password:
        return jsonify({"error": "New password and confirmation do not match"}), 400

    if not _is_valid_password(new_password):
        return jsonify({"error": "Password must be at least 8 characters long and contain at least one letter and one number"}), 400

    db_session = SessionLocal()
    try:
        user_id = int(get_jwt_identity())
        user = db_session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": USER_NOT_FOUND}), 404

        if not check_password_hash(user.password, current_password):
            return jsonify({"error": "Current password is incorrect"}), 400

        if check_password_hash(user.password, new_password):
            return jsonify({"error": "New password must be different from current password"}), 400

        user.password = generate_password_hash(new_password)
        db_session.commit()

        return jsonify({"message": "Password changed successfully"}), 200

    except SQLAlchemyError:
        db_session.rollback()
        return jsonify({"error": INTERNAL_SERVER_ERROR}), 500
    finally:
        db_session.close()

@admin_bp.route("/admin/me", methods=["GET"])
@jwt_required()
@log_route(include_request_data=True)
@log_database_operation("READ")
def get_admin_info():
    """
    Return the authenticated admin user's profile and associated structures.

    Admin-only access (requires role: admin). Requires a valid JWT (identity is the user id). Queries the database for the user and their AdminStructure->Structure associations and returns a JSON response with the user's fields and a list of structures.

    Returns:
        tuple: (Flask Response, int) JSON payload and HTTP status code.
            Success (200) JSON structure:
                {
                    "id": int,
                    "username": str,
                    "name": str | None,
                    "surname": str | None,
                    "email": str | None,
                    "telephone": str | None,
                    "role": str,
                    "structures": [{"id": int, "name": str}, ...]
                }
            Access denied (403): {"error": "Access denied"}
            Not found (404): {"error": "User not found"}
    """
    # Check admin role before proceeding
    try:
        claims = get_jwt()
        user_role = claims.get("role", "").lower()
        if user_role != "admin":
            return jsonify({"error": "Access denied"}), 403
    except Exception:
        return jsonify({"error": "Access denied"}), 403

    db_session = SessionLocal()
    try:
        user_id = int(get_jwt_identity())
        user = db_session.query(User).filter_by(id=int(user_id)).first()
        if not user:
            return jsonify({"error": USER_NOT_FOUND}), 404

        structures_query = get_user_structures_query(db_session, user.id)
        structures = structures_query.all()
        structures_list = [{"id": s.id_structure, "name": s.name} for s in structures]

        return jsonify({
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "surname": user.surname,
            "email": user.email,
            "telephone": user.telephone,
            "role": user.role.name,
            "structures": structures_list
        }), 200
    finally:
        db_session.close()


@admin_bp.route("/admin/portale-alloggi", methods=["GET"])
@jwt_required()
@log_route(include_request_data=True)
@log_database_operation("READ")
def get_portale_alloggi_config():
    """
    Get Portale Alloggi configuration for the current user.

    Returns:
        JSON response with Portale Alloggi credentials (password masked)
    """
    error_response, error_code = verify_admin_access()
    if error_response:
        return error_response, error_code

    try:
        user_id = int(get_jwt_identity())
        db_session = SessionLocal()

        user = db_session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": USER_NOT_FOUND}), 404

        return jsonify({
            "message": "Portale Alloggi configuration retrieved successfully",
            "config": user.to_dict(include_portale_credentials=True)
        }), 200

    except Exception as e:
        return handle_database_error(e, "Portale Alloggi config retrieval")
    finally:
        db_session.close()


@admin_bp.route("/admin/portale-alloggi", methods=["POST"])
@jwt_required()
@log_route(include_request_data=True)
@log_database_operation("UPDATE")
def update_portale_alloggi_config():
    """
    Update Portale Alloggi configuration for the current user.

    Expected JSON payload:
    {
        "portale_username": "string",
        "portale_password": "string",  # Will be encrypted
        "portale_wskey": "string"
    }

    Returns:
        JSON response with success message
    """
    error_response, error_code = verify_admin_access()
    if error_response:
        return error_response, error_code

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        user_id = int(get_jwt_identity())
        db_session = SessionLocal()

        user = db_session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": USER_NOT_FOUND}), 404

        # Update Portale Alloggi credentials
        if "portale_username" in data:
            user.portale_username = data["portale_username"]

        if "portale_password" in data and data["portale_password"]:
            # Encrypt the password before storing
            user.portale_password = encrypt_password(data["portale_password"])

        if "portale_wskey" in data:
            user.portale_wskey = data["portale_wskey"]

        db_session.commit()

        return jsonify({
            "message": "Portale Alloggi configuration updated successfully",
            "config": user.to_dict(include_portale_credentials=True)
        }), 200

    except Exception as e:
        db_session.rollback()
        return handle_database_error(e, "Portale Alloggi config update")
    finally:
        db_session.close()


@admin_bp.route("/admin/portale-alloggi/test", methods=["POST"])
@jwt_required()
@log_route(include_request_data=True)
@log_performance(threshold_ms=5000)
def test_portale_alloggi_connection():
    """
    Test Portale Alloggi connection with current credentials.

    Returns:
        JSON response with test results
    """
    error_response, error_code = verify_admin_access()
    if error_response:
        return error_response, error_code

    try:
        user_id = int(get_jwt_identity())
        db_session = SessionLocal()

        user = db_session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": USER_NOT_FOUND}), 404

        # Check if credentials are configured
        if not user.portale_username or not user.portale_password or not user.portale_wskey:
            return jsonify({
                "error": PORTALE_CREDENTIALS_NOT_CONFIGURED,
                "details": "Please configure username, password, and wskey first"
            }), 400

        # Decrypt password for testing
        decrypted_password = decrypt_password(user.portale_password)

        # Import and test Portale Alloggi service
        try:

            # Initialize service with credentials
            portale_service = PortaleAlloggiService(
                username=user.portale_username,
                password=decrypted_password,
                ws_key=user.portale_wskey
            )

            # Test authentication
            token = portale_service.authenticate()

            if token:
                return jsonify({
                    "message": "Portale Alloggi connection successful",
                    "status": "success",
                    "token_received": True
                }), 200
            return jsonify({
                "error": "Portale Alloggi authentication failed",
                "status": "error",
                "details": "Unable to obtain authentication token"
            }), 400

        except ImportError:
            return jsonify({
                "error": "Portale Alloggi service not available",
                "status": "error",
                "details": "Service module not found"
            }), 500
        except Exception as service_error:
            return jsonify({
                "error": "Portale Alloggi connection failed",
                "status": "error",
                "details": str(service_error)
            }), 400

    except Exception as e:
        return handle_database_error(e, "Portale Alloggi connection test")
    finally:
        db_session.close()


def _prepare_reservation_data(reservation):
    """Helper function to prepare reservation data for Portale Alloggi submission."""
    # Calculate duration in days
    duration = 3  # Default fallback
    if reservation.start_date and reservation.end_date:
        duration = (reservation.end_date - reservation.start_date).days
        # Ensure minimum of 1 day
        duration = max(1, duration)

    return {
        'id': reservation.id,
        'id_reference': reservation.id_reference,
        'start_date': reservation.start_date,
        'end_date': reservation.end_date,
        'duration': duration,
        'name_reference': reservation.name_reference,
        'email': reservation.email,
        'telephone': reservation.telephone
    }


@admin_bp.route("/admin/reservations/<int:reservation_id>/send-to-portale-alloggi", methods=["POST"])
@jwt_required()
@log_route(include_request_data=True, include_response_data=True)
@log_performance(threshold_ms=10000)
def send_reservation_to_portale_alloggi(reservation_id):
    """
    Send guest data from a reservation to Portale Alloggi.

    Args:
        reservation_id (int): ID of the reservation to send

    Returns:
        JSON response with submission results
    """
    error_response, error_code = verify_admin_access()
    if error_response:
        return error_response, error_code

    try:
        user_id = int(get_jwt_identity())
        db_session = SessionLocal()

        # Get user with Portale Alloggi credentials
        user = db_session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": USER_NOT_FOUND}), 404

        # Check if Portale Alloggi is configured
        if not user.portale_username or not user.portale_password or not user.portale_wskey:
            return jsonify({
                "error": PORTALE_CREDENTIALS_NOT_CONFIGURED,
                "details": "Please configure Portale Alloggi credentials in Settings first"
            }), 400

        # Get reservation with clients
        reservation = db_session.query(Reservation).filter(Reservation.id == reservation_id).first()
        if not reservation:
            return jsonify({"error": RESERVATION_NOT_FOUND}), 404

        # Check if reservation is approved
        if reservation.status != 'Approved':
            return jsonify({
                "error": "Reservation not approved",
                "details": "Only approved reservations can be sent to Portale Alloggi"
            }), 400

        # Get all clients for this reservation
        clients = (
            db_session.query(Client)
            .join(ClientReservations, Client.id == ClientReservations.id_client)
            .filter(ClientReservations.id_reservation == reservation_id)
            .all()
        )

        if not clients:
            return jsonify({
                "error": "No guests found",
                "details": "No guest data available for this reservation"
            }), 400

        # Initialize Portale Alloggi service
        decrypted_password = decrypt_password(user.portale_password)
        portale_service = PortaleAlloggiService(
            username=user.portale_username,
            password=decrypted_password,
            ws_key=user.portale_wskey
        )

        # Prepare data for submission
        clients_data = [client.to_dict() for client in clients]
        reservation_data = _prepare_reservation_data(reservation)

        # Test submission to Portale Alloggi (using test endpoint)
        result = portale_service.test_guest_registration(clients_data, reservation_data)

        if result.get('success', False):
            # DO NOT update submission status for test mode
            # Test submissions should not disable buttons or track as sent

            return jsonify({
                "message": "Guest data successfully tested with Portale Alloggi (TEST MODE)",
                "result": result,
                "submission_tracked": False
            }), 200
        return jsonify({
            "error": "Failed to test data with Portale Alloggi",
            "details": result.get('error', 'Unknown error'),
            "result": result
        }), 400

    except Exception as e:
        return handle_database_error(e, "Portale Alloggi reservation submission", reservation_id=reservation_id)
    finally:
        db_session.close()


@admin_bp.route("/admin/reservations/<int:reservation_id>/send-to-portale-alloggi-real", methods=["POST"])
@jwt_required()
@log_route(include_request_data=True, include_response_data=True)
@log_performance(threshold_ms=10000)
def send_reservation_to_portale_alloggi_real(reservation_id):
    """
    Send guest data from a reservation to Portale Alloggi (REAL PRODUCTION).

    Args:
        reservation_id (int): ID of the reservation to send

    Returns:
        JSON response with submission results
    """
    error_response, error_code = verify_admin_access()
    if error_response:
        return error_response, error_code

    try:
        user_id = int(get_jwt_identity())
        db_session = SessionLocal()

        # Get user with Portale Alloggi credentials
        user = db_session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": USER_NOT_FOUND}), 404

        # Check if Portale Alloggi is configured
        if not user.portale_username or not user.portale_password or not user.portale_wskey:
            return jsonify({
                "error": PORTALE_CREDENTIALS_NOT_CONFIGURED,
                "details": "Please configure Portale Alloggi credentials in Settings first"
            }), 400

        # Get reservation with clients
        reservation = db_session.query(Reservation).filter(Reservation.id == reservation_id).first()
        if not reservation:
            return jsonify({"error": RESERVATION_NOT_FOUND}), 404

        # Check if reservation is approved
        if reservation.status != 'Approved':
            return jsonify({
                "error": "Reservation not approved",
                "details": "Only approved reservations can be sent to Portale Alloggi"
            }), 400

        # Get all clients for this reservation
        clients = (
            db_session.query(Client)
            .join(ClientReservations, Client.id == ClientReservations.id_client)
            .filter(ClientReservations.id_reservation == reservation_id)
            .all()
        )

        if not clients:
            return jsonify({
                "error": "No guests found",
                "details": "No guest data available for this reservation"
            }), 400

        # Initialize Portale Alloggi service
        decrypted_password = decrypt_password(user.portale_password)
        portale_service = PortaleAlloggiService(
            username=user.portale_username,
            password=decrypted_password,
            ws_key=user.portale_wskey
        )

        # Prepare data for submission
        clients_data = [client.to_dict() for client in clients]
        reservation_data = _prepare_reservation_data(reservation)

        # REAL submission to Portale Alloggi (production endpoint)
        result = portale_service.submit_guest_registration(clients_data, reservation_data)

        if result.get('success', False):
            # Update reservation with submission status
            reservation.portale_alloggi_sent = True
            reservation.portale_alloggi_sent_at = datetime.now(timezone.utc)
            reservation.portale_alloggi_response = str(result.get('result', ''))

            db_session.commit()

            return jsonify({
                "message": "Guest data successfully sent to Portale Alloggi (PRODUCTION)",
                "result": result,
                "submission_tracked": True
            }), 200
        return jsonify({
            "error": "Failed to send data to Portale Alloggi",
            "details": result.get('error', 'Unknown error'),
            "result": result
        }), 400

    except Exception as e:
        return handle_database_error(e, "Portale Alloggi reservation submission", reservation_id=reservation_id)
    finally:
        db_session.close()


@admin_bp.route("/admin/reservations/<int:reservation_id>/portale-alloggi-status", methods=["GET"])
@jwt_required()
@log_route(include_request_data=True)
@log_database_operation("READ")
def get_portale_alloggi_status(reservation_id):
    """
    Get Portale Alloggi submission status for a reservation.

    Args:
        reservation_id (int): ID of the reservation to check

    Returns:
        JSON response with submission status
    """
    error_response, error_code = verify_admin_access()
    if error_response:
        return error_response, error_code

    try:
        db_session = SessionLocal()

        # Get reservation
        reservation = db_session.query(Reservation).filter(Reservation.id == reservation_id).first()
        if not reservation:
            return jsonify({"error": RESERVATION_NOT_FOUND}), 404

        return jsonify({
            "portale_alloggi_sent": reservation.portale_alloggi_sent,
            "portale_alloggi_sent_at": reservation.portale_alloggi_sent_at.isoformat() if reservation.portale_alloggi_sent_at else None,
            "portale_alloggi_response": reservation.portale_alloggi_response
        }), 200

    except Exception as e:
        return handle_database_error(e, "Portale Alloggi status retrieval", reservation_id=reservation_id)
    finally:
        db_session.close()
