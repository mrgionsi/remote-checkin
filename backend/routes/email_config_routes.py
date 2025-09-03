# routes/email_config_routes.py
# pylint: disable=C0301,E0611,E0401,W0718

"""
Email Configuration Routes for handling email configuration requests.

This module defines the routes and logic for managing user email configurations,
including CRUD operations and testing email settings.
"""

import json
import logging
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError
from models import EmailConfig, User
from database import SessionLocal
from email_handler import EmailService
from cryptography.fernet import Fernet
import base64
import os

# Configure logging
logger = logging.getLogger(__name__)

# Create a blueprint for email configuration
email_config_bp = Blueprint("email_config", __name__, url_prefix="/api/v1")

# Email provider presets
EMAIL_PROVIDER_PRESETS = {
    'gmail': {
        'name': 'Gmail',
        'mail_server': 'smtp.gmail.com',
        'mail_port': 587,
        'mail_use_tls': True,
        'mail_use_ssl': False,
        'instructions': 'Use App Password, not regular password. Enable 2FA and generate App Password.'
    },
    'outlook': {
        'name': 'Outlook/Hotmail',
        'mail_server': 'smtp-mail.outlook.com',
        'mail_port': 587,
        'mail_use_tls': True,
        'mail_use_ssl': False,
        'instructions': 'Use your Outlook email and password.'
    },
    'yahoo': {
        'name': 'Yahoo',
        'mail_server': 'smtp.mail.yahoo.com',
        'mail_port': 587,
        'mail_use_tls': True,
        'mail_use_ssl': False,
        'instructions': 'Use App Password for Yahoo accounts.'
    },
    'mailgun': {
        'name': 'Mailgun',
        'mail_server': 'smtp.mailgun.org',
        'mail_port': 587,
        'mail_use_tls': True,
        'mail_use_ssl': False,
        'provider_type': 'mailgun',
        'instructions': 'Use your Mailgun SMTP credentials.'
    },
    'sendgrid': {
        'name': 'SendGrid',
        'mail_server': 'smtp.sendgrid.net',
        'mail_port': 587,
        'mail_use_tls': True,
        'mail_use_ssl': False,
        'provider_type': 'sendgrid',
        'instructions': 'Use your SendGrid API key as password.'
    },
    'custom': {
        'name': 'Custom SMTP',
        'mail_server': '',
        'mail_port': 587,
        'mail_use_tls': True,
        'mail_use_ssl': False,
        'instructions': 'Enter your custom SMTP server details.'
    }
}


def get_encryption_key():
    """Get or create encryption key for email passwords."""
    # First try to get from Flask app config (in-memory)
    key = current_app.config.get('EMAIL_ENCRYPTION_KEY')
    
    if not key:
        # Try to get from environment variable
        import os
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
    """Encrypt password for storage."""
    if not password:
        logger.warning("Password is empty or None")
        return ""
    
    try:
        key = get_encryption_key()
        f = Fernet(key)
        encrypted = f.encrypt(password.encode()).decode()
        logger.info(f"Password encrypted successfully, original length: {len(password)}, encrypted length: {len(encrypted)}")
        return encrypted
    except Exception as e:
        logger.error(f"Failed to encrypt password: {str(e)}")
        raise e


def decrypt_password(encrypted_password: str) -> str:
    """Decrypt password for use."""
    if not encrypted_password:
        raise ValueError("Encrypted password is empty or None")
    
    try:
        key = get_encryption_key()
        logger.info(f"Key type: {type(key)}, Key length: {len(key) if key else 'None'}")
        logger.info(f"Encrypted password first 20 chars: {encrypted_password[:20] if len(encrypted_password) > 20 else encrypted_password}")
        
        f = Fernet(key)
        decrypted = f.decrypt(encrypted_password.encode()).decode()
        logger.info(f"Decryption successful, decrypted length: {len(decrypted)}")
        return decrypted
    except Exception as e:
        logger.error(f"Decryption failed - encrypted_password type: {type(encrypted_password)}, length: {len(encrypted_password) if encrypted_password else 'None'}")
        logger.error(f"Key type: {type(key) if 'key' in locals() else 'None'}")
        logger.error(f"Exception type: {type(e)}, Exception message: '{str(e)}'")
        logger.error(f"Exception args: {e.args if hasattr(e, 'args') else 'No args'}")
        raise e


@email_config_bp.route("/email-config", methods=["GET"])
@jwt_required()
def get_email_config():
    """
    Get current user's email configuration.
    
    Query Parameters:
        include_password (bool): If true, returns decrypted password. Default: false.
    
    Returns:
        JSON response with email configuration or 404 if not found.
    """
    current_user_id = get_jwt_identity()
    session = SessionLocal()
    
    try:
        config = session.query(EmailConfig).filter(
            EmailConfig.user_id == current_user_id,
            EmailConfig.is_active == True
        ).first()
        
        if not config:
            return jsonify({"error": "No email configuration found"}), 404
        
        # Check if password should be included
        include_password = request.args.get('include_password', 'false').lower() == 'true'
        logger.info(f"Email config request - include_password: {include_password}")
        
        if include_password:
            # Return config with decrypted password for editing
            config_dict = config.to_dict(include_password=True)
            try:
                decrypted_password = decrypt_password(config.mail_password)
                config_dict['mail_password'] = decrypted_password
                logger.info(f"Password decrypted successfully, length: {len(decrypted_password)}")
            except Exception as e:
                logger.error(f"Error decrypting password: {str(e)}")
                config_dict['mail_password'] = ""  # Return empty string if decryption fails
            return jsonify(config_dict)
        else:
            # Return config with masked password (default behavior)
            logger.info("Returning config with masked password")
            return jsonify(config.to_dict(include_password=False))
        
    except Exception as e:
        logger.error(f"Error getting email config: {str(e)}")
        return jsonify({"error": "Failed to retrieve email configuration"}), 500
    finally:
        session.close()


@email_config_bp.route("/email-config", methods=["POST"])
@jwt_required()
def create_or_update_email_config():
    """
    Create or update current user's email configuration.
    
    Returns:
        JSON response with success message or error.
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()
    session = SessionLocal()
    
    try:
        # Validate required fields
        required_fields = ["mail_server", "mail_port", "mail_username", "mail_password", "mail_default_sender_email"]
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Find existing config or create new one
        config = session.query(EmailConfig).filter(
            EmailConfig.user_id == current_user_id
        ).first()
        
        if not config:
            config = EmailConfig(user_id=current_user_id)
            session.add(config)
        
        # Update fields
        config.mail_server = data['mail_server']
        config.mail_port = int(data['mail_port'])
        config.mail_use_tls = data.get('mail_use_tls', True)
        config.mail_use_ssl = data.get('mail_use_ssl', False)
        config.mail_username = data['mail_username']
        config.mail_password = encrypt_password(data['mail_password'])
        config.mail_default_sender_name = data.get('mail_default_sender_name', '')
        config.mail_default_sender_email = data['mail_default_sender_email']
        config.provider_type = data.get('provider_type', 'smtp')
        config.provider_config = json.dumps(data.get('provider_config', {}))
        config.is_active = True
        
        session.commit()
        
        return jsonify({
            "message": "Email configuration saved successfully",
            "config": config.to_dict()
        })
        
    except ValueError as e:
        session.rollback()
        return jsonify({"error": f"Invalid data: {str(e)}"}), 400
    except IntegrityError as e:
        session.rollback()
        return jsonify({"error": "Database integrity error"}), 400
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving email config: {str(e)}")
        return jsonify({"error": "Failed to save email configuration"}), 500
    finally:
        session.close()


@email_config_bp.route("/email-config/test", methods=["POST"])
@jwt_required()
def test_email_config():
    """
    Test email configuration by sending a test email.
    
    Returns:
        JSON response with test result.
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()
    session = SessionLocal()
    
    try:
        # Get test email address from request body or query parameter
        test_email = data.get('test_email') if data else None
        if not test_email:
            test_email = request.args.get('test_email')
        if not test_email:
            return jsonify({"error": "Test email address is required"}), 400
        
        # Get user's email config
        config = session.query(EmailConfig).filter(
            EmailConfig.user_id == current_user_id,
            EmailConfig.is_active == True
        ).first()
        
        if not config:
            return jsonify({"error": "No email configuration found"}), 404
        
        # Create temporary email service with user's config
        encryption_key = get_encryption_key()
        email_service = EmailService(config=config, encryption_key=encryption_key)
        
        # Send test email
        test_data = {
            'reservation_number': 'TEST123',
            'guest_name': 'Test User',
            'start_date': '2024-01-01',
            'end_date': '2024-01-03',
            'room_name': 'Test Room'
        }
        
        result = email_service.send_reservation_confirmation(test_email, test_data)
        
        if result['status'] == 'success':
            return jsonify({
                "message": "Test email sent successfully",
                "result": result
            })
        else:
            return jsonify({
                "error": "Failed to send test email",
                "result": result
            }), 400
            
    except Exception as e:
        logger.error(f"Error testing email config: {str(e)}")
        return jsonify({"error": f"Test failed: {str(e)}"}), 500
    finally:
        session.close()


@email_config_bp.route("/email-config/presets", methods=["GET"])
@jwt_required()
def get_email_presets():
    """
    Get available email provider presets.
    
    Returns:
        JSON response with email provider presets.
    """
    return jsonify(EMAIL_PROVIDER_PRESETS)


@email_config_bp.route("/email-config/preset/<preset_name>", methods=["GET"])
@jwt_required()
def get_email_preset(preset_name):
    """
    Get specific email provider preset.
    
    Args:
        preset_name: Name of the preset (gmail, outlook, yahoo, etc.)
    
    Returns:
        JSON response with preset configuration.
    """
    if preset_name not in EMAIL_PROVIDER_PRESETS:
        return jsonify({"error": "Invalid preset name"}), 400
    
    return jsonify(EMAIL_PROVIDER_PRESETS[preset_name])


@email_config_bp.route("/email-config", methods=["DELETE"])
@jwt_required()
def delete_email_config():
    """
    Delete current user's email configuration.
    
    Returns:
        JSON response with success message.
    """
    current_user_id = get_jwt_identity()
    session = SessionLocal()
    
    try:
        config = session.query(EmailConfig).filter(
            EmailConfig.user_id == current_user_id
        ).first()
        
        if not config:
            return jsonify({"error": "No email configuration found"}), 404
        
        session.delete(config)
        session.commit()
        
        return jsonify({"message": "Email configuration deleted successfully"})
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting email config: {str(e)}")
        return jsonify({"error": "Failed to delete email configuration"}), 500
    finally:
        session.close()


@email_config_bp.route("/email-config/migrate", methods=["POST"])
@jwt_required()
def migrate_to_external_provider():
    """
    Migrate from SMTP to external email provider (Mailgun, SendGrid, etc.).
    
    Returns:
        JSON response with migration result.
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()
    session = SessionLocal()
    
    try:
        provider_type = data.get('provider_type')
        if not provider_type:
            return jsonify({"error": "Provider type is required"}), 400
        
        # Get current config
        config = session.query(EmailConfig).filter(
            EmailConfig.user_id == current_user_id
        ).first()
        
        if not config:
            return jsonify({"error": "No email configuration found"}), 404
        
        # Update provider type and configuration
        config.provider_type = provider_type
        
        # Provider-specific configuration
        if provider_type == 'mailgun':
            config.mail_server = 'smtp.mailgun.org'
            config.mail_port = 587
            config.mail_use_tls = True
            config.mail_use_ssl = False
            config.provider_config = json.dumps({
                'domain': data.get('domain'),
                'api_key': data.get('api_key')
            })
        elif provider_type == 'sendgrid':
            config.mail_server = 'smtp.sendgrid.net'
            config.mail_port = 587
            config.mail_use_tls = True
            config.mail_use_ssl = False
            config.provider_config = json.dumps({
                'api_key': data.get('api_key')
            })
        
        session.commit()
        
        return jsonify({
            "message": f"Successfully migrated to {provider_type}",
            "config": config.to_dict()
        })
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error migrating email config: {str(e)}")
        return jsonify({"error": f"Migration failed: {str(e)}"}), 500
    finally:
        session.close()
