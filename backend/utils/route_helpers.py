# pylint: disable=C0301,E0611,E0401,W0718,R0914,R0912
"""
Route helper utilities for common database operations and error handling.

This module provides shared functions to reduce code duplication across route modules.
"""

import logging

from flask import jsonify, has_request_context
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended.exceptions import JWTExtendedException
from app_logging.utils import safe_extra_fields
from models import AdminStructure, Structure

logger = logging.getLogger(__name__)

# Error message constants
INTERNAL_SERVER_ERROR = "Internal server error"
USER_NOT_FOUND = "User not found"
STRUCTURE_NOT_FOUND = "Structure not found"


def handle_database_error(e, operation_name, user_id=None, **extra_fields):
    """
    Handle database errors with consistent logging and response.
    
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
    return jsonify({"error": INTERNAL_SERVER_ERROR}), 500


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
