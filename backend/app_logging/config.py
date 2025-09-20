"""
Centralized logging configuration for the remote check-in system.

This module provides environment-specific logging configurations with support for:
- Development: Colored console output with detailed information
- Production: JSON structured logs with file rotation
- Testing: Minimal logging to avoid test noise
"""

import os
import logging
import logging.handlers
from typing import Optional
from .formatters import JSONFormatter, ColoredFormatter


class LoggingConfig:
    """Centralized logging configuration class."""

    # Log levels mapping
    LOG_LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }


    @classmethod
    def get_environment(cls) -> str:
        """Get current environment from environment variables."""
        # Check multiple environment indicators
        flask_env = os.getenv('FLASK_ENV', '').lower()
        debug_mode = os.getenv('DEBUG', '').lower() in ('true', '1', 'yes')

        # If Flask is in debug mode or FLASK_ENV is development, use development
        if flask_env == 'development' or debug_mode:
            return 'development'
        elif flask_env == 'testing':
            return 'testing'
        else:
            return 'production'

    @classmethod
    def get_log_level(cls) -> int:
        """Get log level from environment variables."""
        level_name = os.getenv('LOG_LEVEL', 'INFO').upper()
        return cls.LOG_LEVELS.get(level_name, logging.INFO)

    @classmethod
    def get_log_directory(cls) -> str:
        """Get log directory path."""
        return os.getenv('LOG_DIRECTORY', 'logs')

    @classmethod
    def should_log_to_file(cls) -> bool:
        """Determine if logs should be written to files."""
        return os.getenv('LOG_TO_FILE', 'true').lower() == 'true'

    @classmethod
    def get_max_log_file_size(cls) -> int:
        """Get maximum log file size in bytes."""
        return int(os.getenv('MAX_LOG_FILE_SIZE', '10485760'))  # 10MB default

    @classmethod
    def get_log_backup_count(cls) -> int:
        """Get number of backup log files to keep."""
        return int(os.getenv('LOG_BACKUP_COUNT', '5'))


def setup_logging(app_name: str = 'remote-checkin') -> None:
    """
    Setup comprehensive logging configuration based on environment.

    Args:
        app_name: Name of the application for log identification
    """
    config = LoggingConfig()
    environment = config.get_environment()
    log_level = config.get_log_level()

    # Clear existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create formatters
    if environment == 'development':
        formatter = ColoredFormatter()
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)

        # Add console handler
        root_logger.addHandler(console_handler)
        root_logger.setLevel(log_level)

        # File handler for development if enabled
        if config.should_log_to_file():
            log_dir = config.get_log_directory()
            os.makedirs(log_dir, exist_ok=True)

            # Use JSON formatter for files even in development
            json_formatter = JSONFormatter(app_name=app_name)

            file_handler = logging.handlers.RotatingFileHandler(
                filename=os.path.join(log_dir, f'{app_name}.log'),
                maxBytes=config.get_max_log_file_size(),
                backupCount=config.get_log_backup_count()
            )
            file_handler.setFormatter(json_formatter)
            file_handler.setLevel(log_level)
            root_logger.addHandler(file_handler)

            # Separate error log file
            error_handler = logging.handlers.RotatingFileHandler(
                filename=os.path.join(log_dir, f'{app_name}-error.log'),
                maxBytes=config.get_max_log_file_size(),
                backupCount=config.get_log_backup_count()
            )
            error_handler.setFormatter(json_formatter)
            error_handler.setLevel(logging.ERROR)
            root_logger.addHandler(error_handler)

    elif environment == 'production':
        # JSON formatter for production
        json_formatter = JSONFormatter(app_name=app_name)

        # Console handler with JSON format
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(json_formatter)
        console_handler.setLevel(log_level)
        root_logger.addHandler(console_handler)

        # File handler with rotation if enabled
        if config.should_log_to_file():
            log_dir = config.get_log_directory()
            os.makedirs(log_dir, exist_ok=True)

            file_handler = logging.handlers.RotatingFileHandler(
                filename=os.path.join(log_dir, f'{app_name}.log'),
                maxBytes=config.get_max_log_file_size(),
                backupCount=config.get_log_backup_count()
            )
            file_handler.setFormatter(json_formatter)
            file_handler.setLevel(log_level)
            root_logger.addHandler(file_handler)

            # Separate error log file
            error_handler = logging.handlers.RotatingFileHandler(
                filename=os.path.join(log_dir, f'{app_name}-error.log'),
                maxBytes=config.get_max_log_file_size(),
                backupCount=config.get_log_backup_count()
            )
            error_handler.setFormatter(json_formatter)
            error_handler.setLevel(logging.ERROR)
            root_logger.addHandler(error_handler)

        root_logger.setLevel(log_level)

    elif environment == 'testing':
        # Minimal logging for tests
        handler = logging.StreamHandler()
        handler.setLevel(logging.WARNING)
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.WARNING)

    # Configure specific loggers
    _configure_third_party_loggers()

    # Log the configuration
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured for environment: {environment}, level: {logging.getLevelName(log_level)}")


def _configure_third_party_loggers() -> None:
    """Configure third-party library loggers to reduce noise."""
    # Reduce SQLAlchemy logging in production
    environment = LoggingConfig.get_environment()
    if environment == 'production':
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
        logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
        logging.getLogger('sqlalchemy.dialects').setLevel(logging.WARNING)

    # Reduce Werkzeug logging
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

    # Configure other third-party loggers as needed
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance configured with the current settings
    """
    return logging.getLogger(name)


