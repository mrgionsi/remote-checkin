# config.py


from dotenv import load_dotenv
import os

# Load the environment variables from .env file
load_dotenv()



"""
Configuration module for the remote check-in system.
This module contains configuration classes for production and testing environments.
"""

class Config:
    """
    Base configuration class for production environment.
    Defines the default configurations used in production.
    """
    # Normal configuration for production
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"


class TestConfig(Config):
    """
    Configuration class for testing environment.
    Inherits from the base Config class and overrides the configurations for testing purposes.
    """
    # Configuration for testing
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"  # In-memory SQLite for testing
    TESTING = True  # Enable testing mode
