from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import Config
from contextlib import contextmanager

# Create the database engine
engine = create_engine(Config.DATABASE_URL, echo=True)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()

# Context manager for database session
@contextmanager
def get_db():
    db = SessionLocal()  # Create a session
    try:
        yield db  # Pass the session to the caller
    finally:
        db.close()  # Ensure session is closed after use
