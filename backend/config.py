
# config.py

class Config:
    # Normal configuration for production
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DATABASE_URL = "postgresql://gionsi:password@192.168.178.15:5444/remotecheckin"


class TestConfig(Config):
    # Configuration for testing
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"  # In-memory SQLite for testing
    TESTING = True  # Enable testing mode
