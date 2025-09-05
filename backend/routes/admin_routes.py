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
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import User, AdminStructure, Structure
from database import SessionLocal

# Blueprint setup
admin_bp = Blueprint("admin", __name__, url_prefix="/api/v1")

@admin_bp.route("/admin/login", methods=["POST"])
def admin_login():
    """
    Authenticates an admin user by verifying credentials and role, returning a JWT token and associated structures on success.

    Returns:
        JSON response with JWT access token, user information, and associated structures if authentication is successful.
        Returns HTTP 400 if username or password is missing, 401 if credentials are invalid, 403 if the user is not an admin, or 500 on server error.
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
    Creates a new admin user with the specified username, password, and role.

    Accepts a JSON request body containing the new user's credentials and optional profile information. Returns a JSON response with the created user's details on success, or an error message if required fields are missing or the username already exists.

    Returns:
        Response: JSON with user info and HTTP 201 on success, or error message with appropriate status code on failure.
    """
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
    Retrieves the authenticated admin user's profile and associated structures.

    Returns:
        200: JSON object containing the user's ID, username, name, surname, role, and a list of associated structures.
        404: If the user is not found.
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
