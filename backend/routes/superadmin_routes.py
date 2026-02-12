# pylint: disable=C0301,E0611,E0401,W0718,R0914,R0912,C0302,R0911,R0801
"""
Superadmin Routes

This module contains all routes for superadmin functionality including:
- Structure management (CRUD operations)
- User management (admin users)
- Association management (user-structure relationships)
- Global oversight and reporting

All routes are registered under the '/api/v1/superadmin' URL prefix and require superadmin role.
"""

import logging

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from werkzeug.security import generate_password_hash

from app_logging.decorators import log_route
from utils.authz import verify_superadmin_access
from utils.route_helpers import handle_database_error, create_user_response_data, build_user_brief
from models import User, AdminStructure, Structure, Reservation, Role
from database import SessionLocal

logger = logging.getLogger(__name__)

# Create Blueprint
superadmin_bp = Blueprint('superadmin', __name__, url_prefix='/api/v1')

# Constants
INTERNAL_SERVER_ERROR = "Internal server error"
JSON_DATA_REQUIRED = "JSON data required"
STRUCTURE_NOT_FOUND = "Structure not found"
USER_NOT_FOUND = "User not found"


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


def parse_boolean_value(value):
    """
    Parse a value to boolean, handling strings, numbers, and other types properly.

    Args:
        value: The value to parse to boolean

    Returns:
        bool: Parsed boolean value
    """
    if isinstance(value, str):
        # Handle string values - check against accepted true values
        return value.lower() in ("true", "1", "yes", "y")
    if isinstance(value, (int, float)):
        # Handle numeric values - non-zero is True
        return value != 0
    # For other types, use standard bool conversion
    return bool(value)


def _validate_user_creation_data(data):
    """Validate user creation data and return error response if invalid."""
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    name = data.get("name", "").strip()
    surname = data.get("surname", "").strip()

    if not username or not password or not name or not surname:
        return None, jsonify({"error": "Username, password, name and surname are required"}), 400

    return {
        'username': username, 'password': password, 'name': name, 'surname': surname,
        'email': data.get("email", "").strip(), 'telephone': data.get("telephone", "").strip(),
        'id_role': data.get("id_role")
    }, None, None


def _validate_association_data(data):
    """Validate association data and return error response if invalid."""
    user_id = data.get("user_id")
    structure_id = data.get("structure_id")

    if not user_id or not structure_id:
        return None, None, jsonify({"error": "user_id and structure_id are required"}), 400

    return user_id, structure_id, None, None


# ============================================================================
# STRUCTURE MANAGEMENT ENDPOINTS
# ============================================================================

@superadmin_bp.route("/superadmin/structures", methods=["GET"])
@jwt_required()
@log_route(include_request_data=True)
def get_structures():
    """
    Get all structures with optional filtering and pagination.

    Superadmin-only endpoint. Returns a list of all structures with their details.
    Supports query parameters: page, per_page, search, is_active.

    Returns:
        JSON response with structures list and pagination info
    """
    error_response, error_code = verify_superadmin_access()
    if error_response:
        return error_response, error_code

    db_session = None
    try:
        db_session = SessionLocal()

        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)  # Max 100 per page
        search = request.args.get('search', '', type=str).strip()
        is_active = request.args.get('is_active', type=str)

        # Build query
        query = db_session.query(Structure)

        # Apply search filter
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (Structure.name.ilike(search_filter)) |
                (Structure.city.ilike(search_filter)) |
                (Structure.street.ilike(search_filter))
            )

        # Apply active filter
        if is_active is not None:
            normalized = is_active.strip().lower() if isinstance(is_active, str) else None
            if normalized not in (None, '', 'all'):
                if normalized in ('true', '1', 'yes', 'y'):
                    query = query.filter(Structure.is_active.is_(True))
                elif normalized in ('false', '0', 'no', 'n'):
                    query = query.filter(Structure.is_active.is_(False))
                # Any other value: skip filtering

        # Get total count
        total = query.count()

        # Apply pagination
        structures = query.offset((page - 1) * per_page).limit(per_page).all()

        return jsonify({
            "structures": [structure.to_dict() for structure in structures],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page
            }
        }), 200

    except Exception as e:
        return handle_database_error(e, "structures retrieval")
    finally:
        if db_session is not None:
            db_session.close()


@superadmin_bp.route("/superadmin/structures", methods=["POST"])
@jwt_required()
@log_route(include_request_data=True)
def create_structure():
    """
    Create a new structure.

    Superadmin-only endpoint. Expects JSON body with required fields: name, street, city, cin.
    Optional field: is_active (defaults to True).

    Returns:
        JSON response with created structure data
    """
    error_response, error_code = verify_superadmin_access()
    if error_response:
        return error_response, error_code

    data = request.get_json()
    if not data:
        return jsonify({"message": "Request data is required"}), 400

    name = data.get("name", "").strip()
    street = data.get("street", "").strip()
    city = data.get("city", "").strip()
    cin = data.get("cin", "").strip()
    # Coerce is_active properly: default to True when absent or None, otherwise parse
    raw_is_active = data.get("is_active", None)
    is_active = True if raw_is_active is None else parse_boolean_value(raw_is_active)

    if not name or not city:
        return jsonify({"message": "Structure name and city are required"}), 400

    db_session = None
    try:
        db_session = SessionLocal()

        # Check if structure with same name and city already exists
        existing = db_session.query(Structure).filter(
            Structure.name == name,
            Structure.city == city
        ).first()

        if existing:
            return jsonify({"message": "A structure with this name and city already exists"}), 400

        new_structure = Structure(
            name=name,
            street=street,
            city=city,
            cin=cin,
            is_active=is_active
        )

        db_session.add(new_structure)
        db_session.commit()

        return jsonify({
            "message": "Structure created successfully",
            "structure": new_structure.to_dict()
        }), 201

    except Exception as e:
        if db_session is not None:
            db_session.rollback()
        return handle_database_error(e, "structure creation", structure_name=name)
    finally:
        if db_session is not None:
            db_session.close()


@superadmin_bp.route("/superadmin/structures/<int:structure_id>", methods=["PUT"])
@jwt_required()
@log_route(include_request_data=True)
def update_structure(structure_id):
    """
    Update an existing structure.

    Superadmin-only endpoint. Expects JSON body with fields to update: name, street, city, cin, is_active.

    Returns:
        JSON response with updated structure data
    """
    error_response, error_code = verify_superadmin_access()
    if error_response:
        return error_response, error_code

    data = request.get_json()
    if not data:
        return jsonify({"error": JSON_DATA_REQUIRED}), 400

    db_session = None
    try:
        db_session = SessionLocal()

        structure = db_session.query(Structure).filter(Structure.id == structure_id).first()
        if not structure:
            return jsonify({"error": STRUCTURE_NOT_FOUND}), 404

        # Update fields if provided
        if "name" in data:
            structure.name = data["name"].strip()
        if "street" in data:
            structure.street = data["street"].strip()
        if "city" in data:
            structure.city = data["city"].strip()
        if "cin" in data:
            structure.cin = data["cin"].strip()
        if "is_active" in data and data["is_active"] is not None:
            structure.is_active = parse_boolean_value(data["is_active"])

        # Validate required fields
        if not structure.name or not structure.city:
            return jsonify({"error": "Name and city are required"}), 400

        db_session.commit()

        return jsonify({
            "message": "Structure updated successfully",
            "structure": structure.to_dict()
        }), 200

    except Exception as e:
        if db_session is not None:
            db_session.rollback()
        return handle_database_error(e, "structure update", structure_id=structure_id)
    finally:
        if db_session is not None:
            db_session.close()


@superadmin_bp.route("/superadmin/structures/<int:structure_id>", methods=["DELETE"])
@jwt_required()
@log_route(include_request_data=True)
def delete_structure(structure_id):
    """
    Archive/deactivate a structure (soft delete).

    Superadmin-only endpoint. Sets is_active to False instead of hard deletion.

    Returns:
        JSON response with success message
    """
    error_response, error_code = verify_superadmin_access()
    if error_response:
        return error_response, error_code

    db_session = None
    try:
        db_session = SessionLocal()

        structure = db_session.query(Structure).filter(Structure.id == structure_id).first()
        if not structure:
            return jsonify({"error": STRUCTURE_NOT_FOUND}), 404

        structure.is_active = False
        db_session.commit()

        return jsonify({
            "message": "Structure archived successfully"
        }), 200

    except Exception as e:
        if db_session is not None:
            db_session.rollback()
        return handle_database_error(e, "structure archiving", structure_id=structure_id)
    finally:
        if db_session is not None:
            db_session.close()


@superadmin_bp.route("/superadmin/structures/<int:structure_id>/restore", methods=["POST"])
@jwt_required()
@log_route(include_request_data=True)
def restore_structure(structure_id):
    """
    Restore/reactivate an archived structure.

    Superadmin-only endpoint. Sets is_active to True.

    Returns:
        JSON response with success message
    """
    error_response, error_code = verify_superadmin_access()
    if error_response:
        return error_response, error_code

    db_session = None
    try:
        db_session = SessionLocal()

        structure = db_session.query(Structure).filter(Structure.id == structure_id).first()
        if not structure:
            return jsonify({"error": STRUCTURE_NOT_FOUND}), 404

        structure.is_active = True
        db_session.commit()

        return jsonify({
            "message": "Structure restored successfully"
        }), 200

    except Exception as e:
        if db_session is not None:
            db_session.rollback()
        return handle_database_error(e, "structure restoration", structure_id=structure_id)
    finally:
        if db_session is not None:
            db_session.close()


# ============================================================================
# USER MANAGEMENT ENDPOINTS
# ============================================================================

@superadmin_bp.route("/superadmin/users", methods=["GET"])
@jwt_required()
@log_route(include_request_data=True)
def get_users():
    """
    Get all admin and superadmin users with optional filtering and pagination.

    Superadmin-only endpoint. Returns a list of all users with admin roles.
    Supports query parameters: page, per_page, search, role.

    Returns:
        JSON response with users list and pagination info
    """
    error_response, error_code = verify_superadmin_access()
    if error_response:
        return error_response, error_code

    db_session = None
    try:
        db_session = SessionLocal()

        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)  # Max 100 per page
        search = request.args.get('search', '', type=str).strip()
        role_filter = request.args.get('role', '', type=str).strip()

        # Build query - only admin and superadmin users
        query = db_session.query(User).join(Role).filter(
            Role.name.in_(['administrator', 'superadmin'])
        )

        # Apply search filter
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (User.name.ilike(search_filter)) |
                (User.surname.ilike(search_filter)) |
                (User.username.ilike(search_filter)) |
                (User.email.ilike(search_filter))
            )

        # Apply role filter
        if role_filter:
            query = query.filter(Role.name == role_filter)

        # Get total count
        total = query.count()

        # Apply pagination
        users = query.offset((page - 1) * per_page).limit(per_page).all()

        # Get user structures for each user
        users_data = []
        for user in users:
            user_dict = user.to_dict()
            user_dict['role'] = user.role.name if user.role else None

            # Get associated structures
            structures = (
                db_session.query(AdminStructure.id_structure, Structure.name)
                .join(Structure, AdminStructure.id_structure == Structure.id)
                .filter(AdminStructure.id_user == user.id)
                .all()
            )
            user_dict['structures'] = [{"id": s.id_structure, "name": s.name} for s in structures]

            users_data.append(user_dict)

        return jsonify({
            "users": users_data,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page
            }
        }), 200

    except Exception as e:
        return handle_database_error(e, "users retrieval")
    finally:
        if db_session is not None:
            db_session.close()


@superadmin_bp.route("/superadmin/users", methods=["POST"])
@jwt_required()
@log_route(include_request_data=False)
def create_user():  # pylint: disable=too-many-return-statements
    """
    Create a new admin user.

    Superadmin-only endpoint. Expects JSON body with required fields: username, password, name, surname.
    Optional fields: email, telephone, id_role (defaults to administrator role).

    Returns:
        JSON response with created user data
    """
    error_response, error_code = verify_superadmin_access()
    if error_response:
        return error_response, error_code

    data = request.get_json()
    if not data:
        return jsonify({"error": JSON_DATA_REQUIRED}), 400

    user_data, error_response, error_code = _validate_user_creation_data(data)
    if error_response:
        return error_response, error_code

    db_session = None
    try:
        db_session = SessionLocal()
        # Validate username and role
        existing_user = db_session.query(User).filter(User.username == user_data['username']).first()
        if existing_user:
            return jsonify({"error": "Username already exists"}), 400

        role = (db_session.query(Role).filter(Role.id == user_data['id_role']).first() if user_data['id_role']
                else db_session.query(Role).filter(Role.name == 'administrator').first())
        if not role:
            return jsonify({"error": "Invalid role specified"}), 400

        # Create user
        hashed_password = generate_password_hash(user_data['password'])
        new_user = User(
            username=user_data['username'], password=hashed_password, name=user_data['name'],
            surname=user_data['surname'], email=user_data['email'], telephone=user_data['telephone'],
            id_role=role.id
        )

        db_session.add(new_user)
        db_session.commit()

        return jsonify(create_user_response_data(new_user, role)), 201

    except Exception as e:
        if db_session is not None:
            db_session.rollback()
        return handle_database_error(e, "user creation", username=user_data['username'])
    finally:
        if db_session is not None:
            db_session.close()


@superadmin_bp.route("/superadmin/users/<int:user_id>", methods=["PUT"])
@jwt_required()
@log_route(include_request_data=True)
def update_user(user_id):
    """
    Update an existing user.

    Superadmin-only endpoint. Expects JSON body with fields to update.
    Password can be updated separately via reset endpoint.

    Returns:
        JSON response with updated user data
    """
    error_response, error_code = verify_superadmin_access()
    if error_response:
        return error_response, error_code

    data = request.get_json()
    if not data:
        return jsonify({"error": JSON_DATA_REQUIRED}), 400

    db_session = None
    try:
        db_session = SessionLocal()

        user = db_session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": USER_NOT_FOUND}), 404

        # Update fields if provided
        if "name" in data:
            user.name = data["name"].strip()
        if "surname" in data:
            user.surname = data["surname"].strip()
        if "email" in data:
            user.email = data["email"].strip()
        if "telephone" in data:
            user.telephone = data["telephone"].strip()
        if "username" in data:
            new_username = data["username"].strip()
            # Check if new username is already taken by another user
            existing = db_session.query(User).filter(
                User.username == new_username,
                User.id != user_id
            ).first()
            if existing:
                return jsonify({"error": "Username already exists"}), 400
            user.username = new_username

        db_session.commit()

        return jsonify({
            "message": "User updated successfully",
            "user": user.to_dict()
        }), 200

    except Exception as e:
        if db_session is not None:
            db_session.rollback()
        return handle_database_error(e, "user update", user_id=user_id)
    finally:
        if db_session is not None:
            db_session.close()


@superadmin_bp.route("/superadmin/users/<int:user_id>/change-role", methods=["PUT"])
@jwt_required()
@log_route(include_request_data=True)
def change_user_role(user_id):  # pylint: disable=too-many-return-statements
    """
    Change a user's role.

    Superadmin-only endpoint. Expects JSON body with new role id.

    Returns:
        JSON response with success message
    """
    error_response, error_code = verify_superadmin_access()
    if error_response:
        return error_response, error_code

    data = request.get_json()
    if not data:
        return jsonify({"error": JSON_DATA_REQUIRED}), 400

    new_role_id = data.get("id_role")
    if not new_role_id:
        return jsonify({"error": "id_role is required"}), 400

    db_session = None
    try:
        db_session = SessionLocal()

        # Verify user exists
        user = db_session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": USER_NOT_FOUND}), 404

        # Verify new role exists and is valid
        new_role = db_session.query(Role).filter(Role.id == new_role_id).first()
        if not new_role:
            return jsonify({"error": "Invalid role specified"}), 400

        # Validate role is admin or superadmin
        if new_role.name not in ['administrator', 'superadmin']:
            return jsonify({"error": "Role must be administrator or superadmin"}), 400

        # Update user role
        old_role_name = user.role.name if user.role else None
        user.id_role = new_role_id
        db_session.commit()

        user_brief = build_user_brief(user)
        user_brief["role"] = new_role.name

        return jsonify({
            "message": f"User role changed successfully from {old_role_name} to {new_role.name}",
            "user": user_brief
        }), 200

    except Exception as e:
        if db_session is not None:
            db_session.rollback()
        return handle_database_error(e, "role change", user_id=user_id)
    finally:
        if db_session is not None:
            db_session.close()


@superadmin_bp.route("/superadmin/users/<int:user_id>/reset-password", methods=["POST"])
@jwt_required()
@log_route(include_request_data=False)
def reset_user_password(user_id):
    """
    Reset a user's password.

    Superadmin-only endpoint. Expects JSON body with new password.

    Returns:
        JSON response with success message
    """
    error_response, error_code = verify_superadmin_access()
    if error_response:
        return error_response, error_code

    data = request.get_json()
    if not data:
        return jsonify({"error": JSON_DATA_REQUIRED}), 400

    new_password = data.get("password", "").strip()
    if not new_password:
        return jsonify({"error": "Password is required"}), 400
    if not _is_valid_password(new_password):
        return jsonify({"error": "Password must be at least 8 characters long and contain at least one letter and one number"}), 400

    db_session = None
    try:
        db_session = SessionLocal()

        user = db_session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": USER_NOT_FOUND}), 404

        # Hash new password
        user.password = generate_password_hash(new_password)
        db_session.commit()

        return jsonify({
            "message": "Password reset successfully"
        }), 200

    except Exception as e:
        if db_session is not None:
            db_session.rollback()
        return handle_database_error(e, "password reset", user_id=user_id)
    finally:
        if db_session is not None:
            db_session.close()


# ============================================================================
# ROLE MANAGEMENT ENDPOINTS
# ============================================================================

@superadmin_bp.route("/superadmin/roles", methods=["GET"])
@jwt_required()
@log_route(include_request_data=True)
def get_roles():
    """
    Get all available roles.

    Superadmin-only endpoint. Returns a list of all roles in the system.

    Returns:
        JSON response with roles list
    """
    error_response, error_code = verify_superadmin_access()
    if error_response:
        return error_response, error_code

    db_session = None
    try:
        db_session = SessionLocal()

        # Get all roles
        roles = db_session.query(Role).all()
        roles_data = [role.to_dict() for role in roles]

        return jsonify({"roles": roles_data}), 200

    except Exception as e:
        return handle_database_error(e, "roles retrieval")
    finally:
        if db_session is not None:
            db_session.close()


# ============================================================================
# ASSOCIATION MANAGEMENT ENDPOINTS
# ============================================================================

@superadmin_bp.route("/superadmin/associations", methods=["GET"])
@jwt_required()
@log_route(include_request_data=True)
def get_associations():
    """
    Get user-structure associations with optional filtering.

    Superadmin-only endpoint. Supports query parameters: user_id, structure_id.

    Returns:
        JSON response with associations list
    """
    error_response, error_code = verify_superadmin_access()
    if error_response:
        return error_response, error_code

    db_session = None
    try:
        db_session = SessionLocal()

        user_id = request.args.get('user_id', type=int)
        structure_id = request.args.get('structure_id', type=int)

        # Build query
        query = db_session.query(AdminStructure, User, Structure).join(
            User, AdminStructure.id_user == User.id
        ).join(
            Structure, AdminStructure.id_structure == Structure.id
        )

        # Apply filters
        if user_id:
            query = query.filter(AdminStructure.id_user == user_id)
        if structure_id:
            query = query.filter(AdminStructure.id_structure == structure_id)

        associations = query.all()

        result = []
        for assoc, user, structure in associations:
            result.append({
                "user_id": assoc.id_user,
                "structure_id": assoc.id_structure,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "name": user.name,
                    "surname": user.surname
                },
                "structure": {
                    "id": structure.id,
                    "name": structure.name,
                    "city": structure.city
                }
            })

        return jsonify({"associations": result}), 200

    except Exception as e:
        return handle_database_error(e, "associations retrieval")
    finally:
        if db_session is not None:
            db_session.close()


@superadmin_bp.route("/superadmin/associations", methods=["POST"])
@jwt_required()
@log_route(include_request_data=True)
def create_association():  # pylint: disable=too-many-return-statements
    """
    Create a user-structure association.

    Superadmin-only endpoint. Expects JSON body with user_id and structure_id.

    Returns:
        JSON response with success message
    """
    error_response, error_code = verify_superadmin_access()
    if error_response:
        return error_response, error_code

    data = request.get_json()
    if not data:
        return jsonify({"error": JSON_DATA_REQUIRED}), 400

    user_id, structure_id, error_response, error_code = _validate_association_data(data)
    if error_response:
        return error_response, error_code

    db_session = None
    try:
        db_session = SessionLocal()
        # Validate user, structure, and check for existing association
        user = db_session.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(
                "Attempt to create association with non-existent user",
                extra={'user_id': user_id, 'structure_id': structure_id, 'operation': 'create_association'}
            )
            return jsonify({"error": USER_NOT_FOUND}), 404

        structure = db_session.query(Structure).filter(Structure.id == structure_id).first()
        if not structure:
            logger.warning(
                "Attempt to create association with non-existent structure",
                extra={'user_id': user_id, 'structure_id': structure_id, 'operation': 'create_association'}
            )
            return jsonify({"error": STRUCTURE_NOT_FOUND}), 404

        existing = db_session.query(AdminStructure).filter(
            AdminStructure.id_user == user_id, AdminStructure.id_structure == structure_id
        ).first()
        if existing:
            logger.warning(
                "Attempt to create duplicate association",
                extra={
                    'user_id': user_id,
                    'structure_id': structure_id,
                    'user_username': user.username,
                    'structure_name': structure.name,
                    'operation': 'create_association',
                    'result': 'duplicate_rejected'
                }
            )
            return jsonify({"error": "Association already exists"}), 400

        # Create association
        new_association = AdminStructure(id_user=user_id, id_structure=structure_id)
        db_session.add(new_association)
        db_session.commit()

        logger.info(
            "Association created successfully",
            extra={
                'user_id': user_id,
                'structure_id': structure_id,
                'user_username': user.username,
                'structure_name': structure.name,
                'operation': 'create_association',
                'result': 'success'
            }
        )

        return jsonify({"message": "Association created successfully"}), 201

    except Exception as e:
        if db_session is not None:
            db_session.rollback()
        return handle_database_error(e, "association creation", target_user_id=user_id, target_structure_id=structure_id)
    finally:
        if db_session is not None:
            db_session.close()


@superadmin_bp.route("/superadmin/associations", methods=["DELETE"])
@jwt_required()
@log_route(include_request_data=True)
def delete_association():
    """
    Delete a user-structure association.

    Superadmin-only endpoint. Expects JSON body with user_id and structure_id.

    Returns:
        JSON response with success message
    """
    error_response, error_code = verify_superadmin_access()
    if error_response:
        return error_response, error_code

    data = request.get_json()
    if not data:
        return jsonify({"error": JSON_DATA_REQUIRED}), 400

    user_id = data.get("user_id")
    structure_id = data.get("structure_id")

    if not user_id or not structure_id:
        return jsonify({"error": "user_id and structure_id are required"}), 400

    db_session = None
    try:
        db_session = SessionLocal()

        # Find and delete association
        association = db_session.query(AdminStructure).filter(
            AdminStructure.id_user == user_id,
            AdminStructure.id_structure == structure_id
        ).first()

        if not association:
            return jsonify({"error": "Association not found"}), 404

        db_session.delete(association)
        db_session.commit()

        return jsonify({
            "message": "Association deleted successfully"
        }), 200

    except Exception as e:
        if db_session is not None:
            db_session.rollback()
        return handle_database_error(e, "association deletion", target_user_id=user_id, target_structure_id=structure_id)
    finally:
        if db_session is not None:
            db_session.close()


# ============================================================================
# DASHBOARD/OVERVIEW ENDPOINTS
# ============================================================================

@superadmin_bp.route("/superadmin/dashboard", methods=["GET"])
@jwt_required()
@log_route(include_request_data=True)
def get_dashboard_data():
    """
    Get dashboard data for superadmin overview.

    Superadmin-only endpoint. Returns counts and basic statistics.

    Returns:
        JSON response with dashboard data
    """
    error_response, error_code = verify_superadmin_access()
    if error_response:
        return error_response, error_code

    db_session = None
    try:
        db_session = SessionLocal()

        # Get counts
        total_structures = db_session.query(Structure).count()
        active_structures = db_session.query(Structure).filter(Structure.is_active.is_(True)).count()
        total_users = db_session.query(User).join(Role).filter(
            Role.name.in_(['administrator', 'superadmin'])
        ).count()
        total_reservations = db_session.query(Reservation).count()

        # Get unassigned admins (users with no structure associations)
        unassigned_admins = db_session.query(User).join(Role).filter(
            Role.name == 'administrator'
        ).outerjoin(AdminStructure).filter(AdminStructure.id_user.is_(None)).count()

        return jsonify({
            "dashboard": {
                "total_structures": total_structures,
                "active_structures": active_structures,
                "archived_structures": total_structures - active_structures,
                "total_users": total_users,
                "unassigned_admins": unassigned_admins,
                "total_reservations": total_reservations
            }
        }), 200

    except Exception as e:
        return handle_database_error(e, "dashboard data retrieval")
    finally:
        if db_session is not None:
            db_session.close()
