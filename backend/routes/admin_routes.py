from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import User, Role, AdminStructure, Structure
from database import SessionLocal
from datetime import timedelta
import logging

# Blueprint setup
admin_bp = Blueprint("admin", __name__, url_prefix="/api/v1")

@admin_bp.route("/admin/login", methods=["POST"])
def admin_login():
    """
    Authenticate an admin user.

    Request Body:
        - username (str): The admin's username.
        - password (str): The admin's password.

    Returns:
        - 200: JSON with JWT token, user info and associated structures if credentials are valid and user is admin.
        - 400: If username or password is missing.
        - 401: If credentials are invalid.
        - 403: If user is not an admin.
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
                "structures": structures_list,
                "role": user.role.name
            }
        }), 200

    except Exception as e:
        logging.error(f"Errore durante il login: {str(e)}")
        return jsonify({"error": f"Errore durante il login: {str(e)}"}), 500
    finally:
        db_session.close()

@admin_bp.route("/admin/create", methods=["POST"])
def create_admin_user():
    """
    Create a new admin user.

    Request Body (JSON):
        - username (str): The new user's username (required)
        - password (str): The new user's password (required)
        - name (str): The new user's name (optional)
        - surname (str): The new user's surname (optional)
        - id_role (int): Role ID (required, e.g. 2 for superadmin)

    Returns:
        - 201: JSON with created user info
        - 400: If required fields are missing or user exists
        - 500: On server error
    """
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    name = data.get("name")
    surname = data.get("surname")
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
                "id_role": new_user.id_role
            }
        }), 201

    except Exception as e:
        logging.error(f"Errore durante la creazione utente: {str(e)}")
        return jsonify({"error": f"Errore durante la creazione utente: {str(e)}"}), 500
    finally:
        db_session.close()

@admin_bp.route("/admin/me", methods=["GET"])
@jwt_required()
def get_admin_info():
    """
    Get the logged-in admin user's information.

    Returns:
        - 200: JSON with user info and associated structures.
        - 404: If user is not found.
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
            "role": user.role.name,
            "structures": structures_list
        }), 200
    finally:
        db_session.close()