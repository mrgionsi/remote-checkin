# pylint: disable=C0301,E0611,E0401,W0718

"""Admin routes module for user authentication, account creation, and profile retrieval.

This module defines Flask routes related to administrative user actions. It includes:
- Authentication endpoint for admin users with JWT token issuance.
- Endpoint for creating new admin users with role assignments.
- Endpoint for retrieving the currently authenticated admin user's profile and associated structures.

All routes are registered under the '/api/v1/admin' URL prefix and require appropriate user roles
(e.g., admin, superadmin) for access.
"""

from datetime import timedelta
import logging
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, verify_jwt_in_request, get_jwt
from models import User, AdminStructure, Structure
from database import SessionLocal

# Blueprint setup
admin_bp = Blueprint("admin", __name__, url_prefix="/api/v1")

@admin_bp.route("/admin/login", methods=["POST"])
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
        structures = (
            db_session.query(AdminStructure.id_structure, Structure.name)
            .join(Structure, AdminStructure.id_structure == Structure.id)
            .filter(AdminStructure.id_user == user.id)
            .all()
        )
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
        logging.error("Errore durante il login: %s", e)
        return jsonify({"error": f"Errore durante il login: {str(e)}"}), 500
    finally:
        db_session.close()

@admin_bp.route("/admin/create", methods=["POST"])
def create_admin_user():
    """
    Create a new admin user from a JSON request.
    
    Requires JWT authentication and admin role. Expects a JSON body with required fields: `username`, `password`, and `id_role`; optional fields: `name`, `surname`, `email`, and `telephone`. On success inserts a new User record (password is stored hashed) and returns HTTP 201 with the created user's data (id, username, name, surname, email, telephone, id_role). Returns HTTP 400 when required fields are missing or the username already exists, HTTP 401 for missing/invalid JWT, HTTP 403 for insufficient permissions, and HTTP 500 for unexpected server errors.
    """
    # Verify JWT authentication
    try:
        verify_jwt_in_request()
    except Exception:
        return jsonify({"error": "Token di autenticazione mancante o non valido"}), 401
    
    # Check admin role
    try:
        claims = get_jwt()
        user_role = claims.get("role", "").lower()
        if user_role not in ["admin", "superadmin", "administrator"]:
            return jsonify({"error": "Permessi insufficienti. È richiesto un ruolo amministratore"}), 403
    except Exception:
        return jsonify({"error": "Errore durante la verifica dei permessi"}), 403
    
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    name = data.get("name")
    surname = data.get("surname")
    email = data.get("email")
    telephone = data.get("telephone")
    id_role = data.get("id_role")

    if not username or not password or not id_role:
        return jsonify({"error": "username, password e id_role sono obbligatori"}), 400

    db_session = SessionLocal()
    try:
        if db_session.query(User).filter_by(username=username).first():
            return jsonify({"error": "Username gia' esistente"}), 400

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

        return jsonify({
            "message": "Utente creato con successo",
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "name": new_user.name,
                "surname": new_user.surname,
                "email": new_user.email,
                "telephone": new_user.telephone,
                "id_role": new_user.id_role
            }
        }), 201

    except Exception as e:
        db_session.rollback()
        logging.error("Errore durante la creazione utente: %s", e)
        return jsonify({"error": f"Errore durante la creazione utente: {str(e)}"}), 500
    finally:
        db_session.close()

@admin_bp.route("/admin/me", methods=["GET"])
@jwt_required()
def get_admin_info():
    """
    Return the authenticated admin user's profile and associated structures.
    
    Requires a valid JWT (identity is the user id). Queries the database for the user and their AdminStructure->Structure associations and returns a JSON response with the user's fields and a list of structures.
    
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
            Not found (404): {"error": "Utente non trovato"}
    """
    db_session = SessionLocal()
    try:
        user_id = get_jwt_identity()
        user = db_session.query(User).filter_by(id=int(user_id)).first()
        if not user:
            return jsonify({"error": "Utente non trovato"}), 404

        structures = (
            db_session.query(AdminStructure.id_structure, Structure.name)
            .join(Structure, AdminStructure.id_structure == Structure.id)
            .filter(AdminStructure.id_user == user.id)
            .all()
        )
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
