"""
Database module for the remote check-in system.
This module provides configuration for SQLAlchemy, including session management,
engine creation, and a context manager for database operations.
"""

from contextlib import contextmanager  # Standard library import
from sqlalchemy import create_engine  # Third-party imports
from sqlalchemy.orm import sessionmaker, declarative_base  # Third-party imports
#pylint: disable=E0401
from config import Config  # Adjust the path based on your project structure
#pylint: disable=C0301

# Create the database engine
engine = create_engine(
    Config.DATABASE_URL,
    echo=True
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()


# Context manager for database session
@contextmanager
def get_db():
    """
    Context manager that yields a SQLAlchemy database session.

    This generator function creates a new session using SessionLocal, yields it for use within a context,
    and ensures that the session is properly closed after usage. It is intended to provide a transactional
    scope for database operations.

    Yields:
        Session: A SQLAlchemy session instance for database operations.

    Usage Example:
        with get_db() as db:
            # Perform database operations using db
    """
    db = SessionLocal()  # Create a session
    try:
        yield db  # Pass the session to the caller
    finally:
        db.close()  # Ensure session is closed after use
