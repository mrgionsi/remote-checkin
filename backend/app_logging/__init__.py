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
from .middleware import LoggingMiddleware
from .decorators import log_function, log_route
from .formatters import JSONFormatter, ColoredFormatter

__all__ = [
    'setup_logging',
    'get_logger',
    'LoggingMiddleware',
    'log_function',
    'log_route',
    'JSONFormatter',
    'ColoredFormatter'
]
