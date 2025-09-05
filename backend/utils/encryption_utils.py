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
    Return a Fernet-compatible encryption key from app config or environment, creating and caching one if needed.
    
    Checks current_app.config['EMAIL_ENCRYPTION_KEY'] first. If missing, attempts to read the string value from the EMAIL_ENCRYPTION_KEY environment variable (interpreted as a base64-encoded key and encoded to bytes). If neither is present, generates a new key with Fernet.generate_key() and stores it in current_app.config['EMAIL_ENCRYPTION_KEY'].
    
    Returns:
        bytes: A base64-url-safe 32-byte key suitable for cryptography.fernet.Fernet.
    
    Notes:
        - The key is cached in the Flask app config for the process lifetime.
        - Generating a new key will make previously encrypted passwords unreadable unless the original key is preserved and reused (e.g., via the EMAIL_ENCRYPTION_KEY environment variable).
    """
    # First try to get from Flask app config (in-memory)
    key = current_app.config.get('EMAIL_ENCRYPTION_KEY')

    if not key:
        # Try to get from environment variable
        key_string = os.getenv('EMAIL_ENCRYPTION_KEY')
        print(key_string)
        if key_string:
            # Use the key string directly (Fernet expects base64-encoded string)
            key = key_string.encode('utf-8')
            current_app.config['EMAIL_ENCRYPTION_KEY'] = key
            logger.info("Using EMAIL_ENCRYPTION_KEY from environment variable")
        else:
            # Generate a new key if none exists
            key = Fernet.generate_key()
            current_app.config['EMAIL_ENCRYPTION_KEY'] = key
            logger.warning("Generated new EMAIL_ENCRYPTION_KEY - existing encrypted passwords may not be readable")
            logger.warning("Set EMAIL_ENCRYPTION_KEY environment variable to maintain consistency across restarts")

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
