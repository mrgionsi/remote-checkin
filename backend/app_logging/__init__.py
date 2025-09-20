"""
Logging package for the remote check-in system.

This package provides comprehensive logging infrastructure including:
- Centralized logging configuration
- Request/response middleware
- Function-level logging decorators
- Structured formatters
- Correlation ID support
"""

from .config import setup_logging, get_logger
from .middleware import setup_request_logging
from .decorators import log_function, log_route, log_database_operation, log_performance
from .utils import safe_extra_fields

__all__ = [
    'setup_logging',
    'get_logger',
    'setup_request_logging',
    'log_function',
    'log_route',
    'log_database_operation',
    'log_performance',
    'safe_extra_fields'
]
