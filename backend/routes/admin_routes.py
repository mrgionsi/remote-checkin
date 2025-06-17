from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token
from models import User, Role, AdminStructure
from database import SessionLocal

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

    # Database logic: Find user by username
    try:
        db_session = SessionLocal()
        user = db_session.query(User).filter_by(username=username).first()
        if not user:
            return jsonify({"error": "Credenziali non valide"}), 401

        # Verify password (assuming hashed)
        if not check_password_hash(user.password, password):
            return jsonify({"error": "Credenziali non valide"}), 401

        # Check if user has admin role
        if not user.role or user.role.name.lower() not in ["admin", "superadmin", "administrator"]:
            return jsonify({"error": "Non autorizzato"}), 403

        # Get structures administered by this user
        admin_structures = db_session.query(AdminStructure).filter_by(id_user=user.id).all()
        structures = [astruct.id_structure for astruct in admin_structures]

        # Create JWT token
        access_token = create_access_token(identity={
            "id": user.id,
            "username": user.username,
            "role": user.role.name
        })

        return jsonify({
            "access_token": access_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "name": user.name,
                "surname": user.surname,
                "structures": structures,
                "role": user.role.name
            }
        }), 200

    except Exception as e:
        return jsonify({"error": f"Errore durante il login: {str(e)}"}), 500

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

    try:
        db_session = SessionLocal()
        # Check if user already exists
        if db_session.query(User).filter_by(username=username).first():
            return jsonify({"error": "Username già esistente"}), 400

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Create user
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
        return jsonify({"error": f"Errore durante la creazione utente: {str(e)}"}), 500