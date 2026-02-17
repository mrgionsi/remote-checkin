"""
Database module for the remote check-in system.
This module provides configuration for SQLAlchemy, including session management,
engine creation, and a context manager for database operations.
"""

import os
import sys
from contextlib import contextmanager  # Standard library import
from sqlalchemy import create_engine  # Third-party imports
from sqlalchemy.exc import ArgumentError
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import sessionmaker, declarative_base  # Third-party imports
#pylint: disable=E0401
from config import Config  # Adjust the path based on your project structure
#pylint: disable=C0301

def _is_test_context():
    """Return True when running pytest or explicit testing mode."""
    return (
        "pytest" in sys.modules
        or any("pytest" in arg for arg in sys.argv)
        or os.getenv("PYTEST_CURRENT_TEST") is not None
        or os.getenv("TESTING", "").lower() in {"1", "true", "yes"}
        or os.getenv("FLASK_ENV", "").lower() == "testing"
    )


def _resolve_database_url():
    """Resolve database URL with a safe test fallback."""
    runtime_database_url = os.getenv("DATABASE_URL")
    if runtime_database_url and str(runtime_database_url).strip().lower() != "none":
        try:
            make_url(runtime_database_url)
            return runtime_database_url
        except ArgumentError:
            pass

    if _is_test_context():
        test_database_url = os.getenv("TEST_DATABASE_URL")
        if test_database_url and str(test_database_url).strip().lower() != "none":
            return test_database_url

    return Config.DATABASE_URL


database_url = _resolve_database_url()
engine_kwargs = {
    "echo": os.getenv('DATABASE_ECHO', 'false').lower() == 'true'
}
if database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

# Create the database engine with environment-based echo
engine = create_engine(database_url, **engine_kwargs)

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
