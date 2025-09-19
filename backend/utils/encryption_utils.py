"""
Encryption utilities for the remote check-in system.

This module provides functions for handling encryption keys and password encryption/decryption.
"""
#pylint: disable=C0301,E0611,E0401,W0718,R0914
import os
import logging
from flask import current_app
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


def get_encryption_key():
    """
    Return a Fernet-compatible encryption key from app config or environment.
    
    In production environments, requires an explicit ENCRYPTION_KEY environment variable.
    In development/testing environments, generates a new key if none is provided.
    
    Returns:
        bytes: A base64-url-safe 32-byte key suitable for cryptography.fernet.Fernet.
        
    Raises:
        RuntimeError: If no key is available in production environment.
    
    Notes:
        - The key is cached in the Flask app config for the process lifetime.
        - In production, ENCRYPTION_KEY environment variable is required.
        - In development/testing, a new key is generated if none is provided.
        - This key is used for encrypting sensitive data like email passwords and Portale Alloggi credentials.
    """
    # First try to get from Flask app config (in-memory)
    key = current_app.config.get('ENCRYPTION_KEY')

    if not key:
        # Check environment to determine if we should generate a key
        env = current_app.config.get('ENV') or os.getenv('FLASK_ENV', 'production')
        is_development = env.lower() in ['development', 'testing']

        # Try to get from environment variable (support both old and new names for backward compatibility)
        key_string = os.getenv('ENCRYPTION_KEY') or os.getenv('EMAIL_ENCRYPTION_KEY')
        if key_string:
            # Use the key string directly (Fernet expects base64-encoded string)
            key = key_string.encode('utf-8')
            current_app.config['ENCRYPTION_KEY'] = key
            logger.info("Using ENCRYPTION_KEY from environment variable")
        elif is_development:
            # Generate a new key only in development/testing environments
            key = Fernet.generate_key()
            current_app.config['ENCRYPTION_KEY'] = key
            logger.warning("Generated new ENCRYPTION_KEY for development - existing encrypted passwords may not be readable")
            logger.warning("Set ENCRYPTION_KEY environment variable to maintain consistency across restarts")
        else:
            # Fail fast in production if no key is provided
            error_msg = "ENCRYPTION_KEY environment variable is required in production environment"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    return key


def encrypt_password(password: str) -> str:
    """
    Encrypt a plaintext password for safe storage.
    
    If `password` is falsy (empty or None) this returns an empty string. Otherwise the function
    uses the current encryption key to encrypt the password and returns the base64-encoded result.
    
    Args:
        password (str): The plaintext password to encrypt.
    
    Returns:
        str: Base64-encoded encrypted password, or empty string if password is falsy.
    """
    if not password:
        return ""

    key = get_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(password.encode())
    return encrypted.decode()


def decrypt_password(encrypted_password: str) -> str:
    """
    Decrypt a base64-encoded encrypted password.
    
    Args:
        encrypted_password (str): The base64-encoded encrypted password.
    
    Returns:
        str: The decrypted plaintext password.
    
    Raises:
        Exception: If decryption fails.
    """
    if not encrypted_password:
        return ""

    key = get_encryption_key()
    f = Fernet(key)
    return f.decrypt(encrypted_password.encode()).decode()
