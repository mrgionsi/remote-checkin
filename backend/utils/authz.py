# pylint: disable=C0301,E0611,E0401,W0718
"""
Authorization utilities for route protection.

This module provides shared functions for JWT authentication and role-based access control.
It handles JWT-specific exceptions properly and provides consistent error responses.
"""

from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from flask_jwt_extended.exceptions import (
    NoAuthorizationError,
    InvalidHeaderError,
    JWTDecodeError,
    WrongTokenError,
    RevokedTokenError,
    FreshTokenRequired,
    CSRFError
)

# Error message constants
AUTH_TOKEN_INVALID = "Authentication token missing or invalid"
PERMISSION_ERROR = "Error during permission verification"
ADMIN_ROLE_REQUIRED = "Insufficient permissions. Administrator role required"
SUPERADMIN_ROLE_REQUIRED = "Insufficient permissions. Superadmin role required"


def verify_admin_access():
    """
    Verify JWT authentication and admin role access.
    
    Returns:
        tuple: (error_response, error_code) if verification fails, (None, None) if successful
    """
    # Verify JWT token presence and validity
    try:
        verify_jwt_in_request()
    except (NoAuthorizationError, InvalidHeaderError, JWTDecodeError, WrongTokenError, RevokedTokenError, FreshTokenRequired, CSRFError):
        return jsonify({"error": AUTH_TOKEN_INVALID}), 401
    except Exception:
        # Catch any other unexpected JWT-related errors
        return jsonify({"error": AUTH_TOKEN_INVALID}), 401

    # Verify admin role
    try:
        claims = get_jwt()
        user_role = claims.get("role", "").lower()
        if user_role not in ["admin", "superadmin", "administrator"]:
            return jsonify({"error": ADMIN_ROLE_REQUIRED}), 403
    except Exception:
        return jsonify({"error": PERMISSION_ERROR}), 403

    return None, None


def verify_superadmin_access():
    """
    Verify JWT authentication and superadmin role access.
    
    Returns:
        tuple: (error_response, error_code) if verification fails, (None, None) if successful
    """
    # Verify JWT token presence and validity
    try:
        verify_jwt_in_request()
    except (NoAuthorizationError, InvalidHeaderError, JWTDecodeError, WrongTokenError, RevokedTokenError, FreshTokenRequired, CSRFError):
        return jsonify({"error": AUTH_TOKEN_INVALID}), 401
    except Exception:
        # Catch any other unexpected JWT-related errors
        return jsonify({"error": AUTH_TOKEN_INVALID}), 401

    # Verify superadmin role
    try:
        claims = get_jwt()
        user_role = claims.get("role", "").lower()
        if user_role != "superadmin":
            return jsonify({"error": SUPERADMIN_ROLE_REQUIRED}), 403
    except Exception:
        return jsonify({"error": PERMISSION_ERROR}), 403

    return None, None
