#!/usr/bin/env python3
"""
Generate a persistent encryption key for email password encryption.

This script generates a Fernet encryption key that can be used consistently
across application restarts to encrypt/decrypt email passwords.

Usage:
    python generate_encryption_key.py

Then add the output to your .env file:
    EMAIL_ENCRYPTION_KEY=your_generated_key_here
"""

import base64
import secrets

def generate_encryption_key():
    """
    Generate a new Fernet-compatible encryption key and print installation instructions.
    
    Returns:
        str: URL-safe base64-encoded string representing 32 random bytes (Fernet key). 
        The function also prints a formatted block showing the key and how to add it as EMAIL_ENCRYPTION_KEY in a .env file.
    """
    # Generate 32 random bytes (Fernet key length)
    key_bytes = secrets.token_bytes(32)

    # Convert to base64 string for easier storage in environment variables
    key_string = base64.urlsafe_b64encode(key_bytes).decode('utf-8')

    print("=" * 60)
    print("EMAIL ENCRYPTION KEY GENERATED")
    print("=" * 60)
    print(f"Key (base64): {key_string}")
    print()
    print("Add this to your .env file:")
    print(f"EMAIL_ENCRYPTION_KEY={key_string}")
    print()
    print("IMPORTANT:")
    print("- Keep this key secure and never commit it to version control")
    print("- Use the same key across all environments for consistency")
    print("- If you lose this key, all encrypted passwords will be unreadable")
    print("=" * 60)

    return key_string

if __name__ == "__main__":
    generate_encryption_key()
