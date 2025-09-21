"""
Custom logging formatters for the remote check-in system.

This module provides specialized formatters for different environments:
- JSONFormatter: Structured JSON logs for production
- ColoredFormatter: Colored console output for development
"""

import json
import logging
import traceback
from datetime import datetime, timezone
from typing import Dict, Any
from .utils import get_correlation_id


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging in production environments.

    Outputs logs in JSON format with consistent fields for easy parsing
    by log aggregation systems like ELK stack, Splunk, etc.
    """

    def __init__(self, app_name: str = 'remote-checkin'):
        """
        Initialize JSON formatter.

        Args:
            app_name: Application name to include in logs
        """
        super().__init__()
        self.app_name = app_name

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON formatted log string
        """
        log_data = {
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'app_name': self.app_name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'process_id': record.process,
            'thread_id': record.thread,
        }

        # Add correlation ID if available
        correlation_id = get_correlation_id()
        if correlation_id:
            log_data['correlation_id'] = correlation_id

        # Add exception information if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }

        # Add extra fields from record
        extra_fields = self._get_extra_fields(record)
        if extra_fields:
            log_data['extra'] = extra_fields

        return json.dumps(log_data, ensure_ascii=False, separators=(',', ':'))

    def _get_extra_fields(self, record: logging.LogRecord) -> Dict[str, Any]:
        """
        Extract extra fields from log record.

        Args:
            record: Log record

        Returns:
            Dictionary of extra fields
        """
        # Standard fields that shouldn't be included in extra
        standard_fields = {
            'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
            'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
            'thread', 'threadName', 'processName', 'process', 'exc_info', 'exc_text',
            'stack_info', 'getMessage', 'taskName', 'asctime', 'message'
        }

        extra = {}
        for key, value in record.__dict__.items():
            if key not in standard_fields and not key.startswith('_'):
                try:
                    # Ensure value is JSON serializable
                    json.dumps(value)
                    extra[key] = value
                except (TypeError, ValueError):
                    extra[key] = str(value)

        return extra


class ColoredFormatter(logging.Formatter):
    """
    Colored formatter for development environment console output.

    Provides colored output based on log levels and includes correlation IDs
    for better debugging experience.
    """

    # Color codes for different log levels
    COLORS = {
        logging.DEBUG: '\033[36m',      # Cyan
        logging.INFO: '\033[32m',       # Green
        logging.WARNING: '\033[33m',    # Yellow
        logging.ERROR: '\033[31m',      # Red
        logging.CRITICAL: '\033[35m',   # Magenta
    }

    RESET = '\033[0m'  # Reset color
    BOLD = '\033[1m'   # Bold text

    def __init__(self):
        """Initialize colored formatter with custom format."""
        super().__init__()
        self.base_format = (
            '{color}{bold}[{levelname:8}]{reset} '
            '{timestamp} '
            '{correlation}'
            '{color}{logger}:{function}:{lineno}{reset} - '
            '{message}'
        )

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with colors.

        Args:
            record: Log record to format

        Returns:
            Colored formatted log string
        """
        # Get color for log level
        color = self.COLORS.get(record.levelno, '')

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')

        # Get correlation ID
        correlation_id = get_correlation_id()
        correlation_str = f'[{correlation_id[:8]}] ' if correlation_id else ''

        # Format the message
        formatted_message = self.base_format.format(
            color=color,
            bold=self.BOLD,
            reset=self.RESET,
            levelname=record.levelname,
            timestamp=timestamp,
            correlation=correlation_str,
            logger=record.name.split('.')[-1],  # Show only the last part of logger name
            function=record.funcName,
            lineno=record.lineno,
            message=record.getMessage()
        )

        # Add exception information if present
        if record.exc_info:
            formatted_message += '\n' + self.formatException(record.exc_info)

        return formatted_message
