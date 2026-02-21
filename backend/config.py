"""
Configuration settings for the remote check-in system.

This file contains classes for configuring the production and testing environments.
"""
# pylint: disable=R0903

import os
from typing import ClassVar
from dotenv import load_dotenv

# Load the environment variables from .env file
load_dotenv()


def _get_int_env(name: str, default: int) -> int:
    """Return integer env var value with a safe fallback."""
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    value = str(raw_value).strip()
    if value == "" or value.lower() == "none":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _get_database_url():
    """Return DATABASE_URL when valid, otherwise compose from DB_* variables."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        raw = str(database_url).strip()
        if raw and "os.getenv(" not in raw and "{os.getenv(" not in raw:
            return raw

    required_vars = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"]
    missing_vars = [name for name in required_vars if not str(os.getenv(name, "")).strip()]
    if missing_vars:
        raise ValueError(
            "Missing required database environment variables: "
            + ", ".join(missing_vars)
        )

    return (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )


class Config:
    """
    Base configuration class for production environment.
    Defines the default configurations used in production.
    """

    def __init__(self):
        pass

    # Normal configuration for production
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DATABASE_URL = _get_database_url()

    # Email configuration
    #MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
   # MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    #MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    #MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
    #MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    #MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    #MAIL_DEFAULT_SENDER = (
    #    os.getenv('MAIL_DEFAULT_SENDER_NAME', 'Remote Check-in'),
    #    os.getenv('MAIL_DEFAULT_SENDER_EMAIL')
    #)
    MAIL_MAX_EMAILS = _get_int_env('MAIL_MAX_EMAILS', 100)
    MAIL_ASCII_ATTACHMENTS = os.getenv('MAIL_ASCII_ATTACHMENTS', 'False').lower() == 'true'
    # Email templates
    EMAIL_TEMPLATES: ClassVar[dict] = {
        'reservation_confirmation': {
            'subject': 'Reservation Confirmation - {reservation_number}',
            'template': 'reservation_confirmation.html'
        },
        'reservation_update': {
            'subject': 'Reservation Update - {reservation_number}',
            'template': 'reservation_update.html'
        },
        'reservation_cancellation': {
            'subject': 'Reservation Cancellation - {reservation_number}',
            'template': 'reservation_cancellation.html'
        }
    }


class TestConfig(Config):
    """
    Configuration class for testing environment.
    Inherits from the base Config class and overrides the configurations for testing purposes.
    """

    # Configuration for testing
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"  # In-memory SQLite for testing
    TESTING = True  # Enable testing mode

    # Test email configuration
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 1025
    MAIL_USE_TLS = False
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'test@example.com'
    MAIL_PASSWORD = 'test_password'
    MAIL_DEFAULT_SENDER = ('Test System', 'test@example.com')
