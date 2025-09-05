"""
Email utilities for the remote check-in system.

This module provides common email-related functions used across different routes.
"""

from models import EmailConfig, User, AdminStructure
from database import SessionLocal


def get_admin_email_config(reservation):
    """
    Get the email configuration for the admin of the structure associated with a reservation.
    
    Args:
        reservation: The reservation object containing room information
        
    Returns:
        tuple: (email_config, admin_user) or (None, None) if not found
    """
    email_session = SessionLocal()
    try:
        # Get the structure admin using AdminStructure relationship
        admin_structure = email_session.query(AdminStructure).filter(
            AdminStructure.id_structure == reservation.room.id_structure
        ).first()

        admin_user = None
        if admin_structure:
            admin_user = email_session.query(User).filter(
                User.id == admin_structure.id_user
            ).first()

        if admin_user:
            email_config = email_session.query(EmailConfig).filter(
                EmailConfig.user_id == admin_user.id,
                EmailConfig.is_active.is_(True)
            ).first()
            return email_config, admin_user
        return None, None
    finally:
        email_session.close()
