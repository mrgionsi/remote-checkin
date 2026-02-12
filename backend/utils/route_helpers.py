# pylint: disable=C0301,E0611,E0401,W0718,R0914,R0912,R0801
"""
Route helper utilities for common database operations and error handling.

This module provides shared functions to reduce code duplication across route modules.
"""

import logging

from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended.exceptions import JWTExtendedException
from app_logging.utils import safe_extra_fields
from utils.authz import is_superadmin
from models import AdminStructure, Structure

logger = logging.getLogger(__name__)

# Error message constants
INTERNAL_SERVER_ERROR = "Internal server error"
USER_NOT_FOUND = "User not found"
STRUCTURE_NOT_FOUND = "Structure not found"


def handle_database_error(e, operation_name, user_id=None, **extra_fields):
    """
    Handle database errors with consistent logging and user-friendly response.
    
    Args:
        e: The exception that occurred
        operation_name: Name of the operation that failed
        user_id: Optional user ID for logging
        **extra_fields: Additional fields to include in logging
        
    Returns:
        tuple: (error_response, error_code)
    """
    try:
        jwt_user = get_jwt_identity()
    except JWTExtendedException:  # safe fallback if no request/JWT context
        jwt_user = None

    # Log the technical error details
    logger.error(
        "Error during %s",
        operation_name,
        extra=safe_extra_fields({
            'user_id': user_id or jwt_user,
            'error_type': type(e).__name__,
            'error_details': str(e),
            'operation_result': 'failed',
            **extra_fields
        })
    )

    # Return user-friendly error message
    user_message = get_user_friendly_error_message(e, operation_name)
    return jsonify({"message": user_message}), 500


def get_user_friendly_error_message(e, operation_name):
    """
    Convert technical errors to user-friendly messages.
    
    Args:
        e: The exception that occurred
        operation_name: Name of the operation that failed
        
    Returns:
        str: User-friendly error message
    """
    error_str = str(e).lower()

    # Initialize message with generic fallback
    message = f"An error occurred during {operation_name}. Please try again."

    # Database constraint violations
    if 'unique constraint' in error_str or 'duplicate key' in error_str:
        if 'structure' in operation_name.lower():
            message = "A structure with this name and city already exists."
        elif 'user' in operation_name.lower():
            message = "A user with this username or email already exists."
        else:
            message = "This record already exists."
    # Foreign key violations
    elif 'foreign key constraint' in error_str:
        message = "Cannot perform this action because related data exists."
    # Not null violations
    elif 'not null constraint' in error_str:
        message = "Required information is missing. Please check all required fields."
    # Sequence/table not found
    elif 'does not exist' in error_str:
        message = "Database configuration error. Please contact support."
    # Connection errors
    elif 'connection' in error_str or 'timeout' in error_str:
        message = "Database connection error. Please try again."

    return message

def handle_integrity_error(e, operation_name, user_id=None, **extra_fields):
    """
    Handle integrity constraint errors with consistent logging and response.
    
    Args:
        e: The IntegrityError exception
        operation_name: Name of the operation that failed
        user_id: Optional user ID for logging
        **extra_fields: Additional fields to include in logging
        
    Returns:
        tuple: (error_response, error_code)
    """
    try:
        jwt_user = get_jwt_identity()
    except JWTExtendedException:  # safe fallback if no request/JWT context
        jwt_user = None
    logger.error(
        "Integrity constraint violation during %s",
        operation_name,
        extra=safe_extra_fields({
            'user_id': user_id or jwt_user,
            'error_type': 'integrity_constraint',
            'error_details': str(e),
            'operation_result': 'failed',
            **extra_fields
        }),
        exc_info=True
    )
    return jsonify({"error": f"{operation_name} failed due to data constraint violation"}), 400


def error_response(message, status_code=400):
    """
    Return a standardized JSON error response.
    """
    return jsonify({"error": message}), status_code


def get_current_user_id():
    """
    Parse and return the current JWT identity as int.

    Returns:
        tuple: (user_id, error_tuple)
            - user_id (int | None)
            - error_tuple is None on success, otherwise `(json_response, status_code)`
    """
    try:
        return int(get_jwt_identity()), None
    except (TypeError, ValueError):
        return None, error_response("Invalid user identity", 400)


def require_structure_access(db_session, structure_id, user_id=None, allow_superadmin=True):
    """
    Validate structure access for the current user in a single shared path.

    Returns:
        tuple: (normalized_structure_id, error_tuple)
            - normalized_structure_id (int | None)
            - error_tuple is None on success, otherwise `(json_response, status_code)`
    """
    try:
        normalized_structure_id = int(structure_id)
    except (TypeError, ValueError):
        return None, error_response("Invalid structure_id. Must be an integer.", 400)

    if allow_superadmin and is_superadmin():
        return normalized_structure_id, None

    effective_user_id = user_id
    if effective_user_id is None:
        effective_user_id, user_error = get_current_user_id()
        if user_error:
            return None, user_error

    if not user_has_structure(db_session, effective_user_id, normalized_structure_id):
        return normalized_structure_id, error_response("Access denied for this structure", 403)

    return normalized_structure_id, None


def get_user_structures_query(db_session, user_id):
    """
    Get the query for user-structure associations.
    
    Args:
        db_session: Database session
        user_id: User ID to get structures for
        
    Returns:
        Query object for user structures
    """
    return (
        db_session.query(AdminStructure.id_structure, Structure.name)
        .join(Structure, AdminStructure.id_structure == Structure.id)
        .filter(AdminStructure.id_user == user_id)
    )


def get_user_structure_ids(db_session, user_id):
    """
    Return a list of structure IDs associated with the given user.
    """
    rows = (
        db_session.query(AdminStructure.id_structure)
        .filter(AdminStructure.id_user == user_id)
        .all()
    )
    return [row.id_structure for row in rows]


def user_has_structure(db_session, user_id, structure_id):
    """
    Return True if the user is associated with the given structure ID.
    """
    return (
        db_session.query(AdminStructure)
        .filter(
            AdminStructure.id_user == user_id,
            AdminStructure.id_structure == structure_id
        )
        .first()
        is not None
    )


def create_user_response_data(new_user, role):
    """
    Create standardized user response data.
    
    Args:
        new_user: User object
        role: Role object
        
    Returns:
        dict: User response data
    """
    return {
        "message": "User created successfully",
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "name": new_user.name,
            "surname": new_user.surname,
            "email": new_user.email,
            "telephone": new_user.telephone,
            "role": role.name
        }
    }


def build_user_brief(user):
    """
    Build a brief user dictionary with basic identity fields.

    Args:
        user: User model instance

    Returns:
        dict: Brief user representation
    """
    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "surname": user.surname
    }
