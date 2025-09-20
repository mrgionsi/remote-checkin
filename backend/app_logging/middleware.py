"""
Logging middleware for Flask applications.

This module provides middleware for automatic HTTP request/response logging
with correlation ID support and performance monitoring.
"""

import time
import uuid
import logging
from typing import Optional, Dict, Any, List
from flask import Flask, request, g, jsonify
from flask_jwt_extended import get_jwt_identity
from werkzeug.exceptions import HTTPException

from .config import get_logger


class LoggingMiddleware:
    """
    Flask middleware for comprehensive request/response logging.
    
    Features:
    - Automatic request/response logging
    - Correlation ID generation and tracking
    - Performance monitoring (response time)
    - User identification from JWT tokens
    - Sensitive data filtering
    - Exception logging
    """
    
    # Sensitive fields that should be filtered from logs
    SENSITIVE_FIELDS = {
        'password', 'passwd', 'secret', 'token', 'key', 'authorization',
        'x-api-key', 'x-auth-token', 'cookie', 'session'
    }
    
    # Paths to exclude from detailed logging (health checks, static files, etc.)
    EXCLUDED_PATHS = {
        '/health', '/ping', '/favicon.ico', '/robots.txt'
    }
    
    def __init__(self, app: Optional[Flask] = None, 
                 exclude_paths: Optional[List[str]] = None,
                 log_request_body: bool = True,
                 log_response_body: bool = False,
                 max_body_size: int = 1024):
        """
        Initialize logging middleware.
        
        Args:
            app: Flask application instance
            exclude_paths: Additional paths to exclude from logging
            log_request_body: Whether to log request body
            log_response_body: Whether to log response body
            max_body_size: Maximum body size to log (in bytes)
        """
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.max_body_size = max_body_size
        self.logger = get_logger(__name__)
        
        # Setup request formatter
        self.request_logger = logging.getLogger(f"{__name__}.requests")
        # Request logger will use the same formatters as the main logging system
        # No need for separate handler - let it propagate to root logger
        self.request_logger.propagate = True
        
        # Update excluded paths
        if exclude_paths:
            self.EXCLUDED_PATHS.update(exclude_paths)
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask) -> None:
        """
        Initialize middleware with Flask app.
        
        Args:
            app: Flask application instance
        """
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.errorhandler(Exception)(self._handle_exception)
    
    def _before_request(self) -> Optional[Any]:
        """Process request before handling."""
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        g.correlation_id = correlation_id
        g.request_start_time = time.time()
        
        # Skip logging for excluded paths
        if request.path in self.EXCLUDED_PATHS:
            return None
        
        # Get user information
        user_id = self._get_user_id()
        
        # Prepare request data
        request_data = {
            'correlation_id': correlation_id,
            'method': request.method,
            'path': request.path,
            'remote_addr': self._get_client_ip(),
            'user_agent': request.headers.get('User-Agent', ''),
            'user_id': user_id,
            'query_params': dict(request.args),
        }
        
        # Add request headers (filtered)
        request_data['headers'] = self._filter_sensitive_data(dict(request.headers))
        
        # Add request body if enabled
        if self.log_request_body and request.content_length and request.content_length < self.max_body_size:
            try:
                if request.is_json:
                    body = request.get_json()
                    request_data['body'] = self._filter_sensitive_data(body) if body else None
                elif request.form:
                    request_data['body'] = self._filter_sensitive_data(dict(request.form))
                else:
                    # For other content types, log the raw data (truncated)
                    raw_data = request.get_data(as_text=True)
                    if len(raw_data) <= self.max_body_size:
                        request_data['body'] = raw_data[:self.max_body_size]
            except Exception as e:
                self.logger.warning(f"Failed to log request body: {e}")
        
        # Log the request
        self.logger.info("Incoming request", extra={'request_data': request_data})
        
        # Store request data for response logging
        g.request_data = request_data
        
        return None
    
    def _after_request(self, response) -> Any:
        """Process response after handling."""
        # Skip logging for excluded paths
        if request.path in self.EXCLUDED_PATHS:
            return response
        
        # Calculate response time
        duration = int((time.time() - g.request_start_time) * 1000)  # milliseconds
        
        # Update request data with response information
        request_data = getattr(g, 'request_data', {})
        request_data.update({
            'status_code': response.status_code,
            'duration': duration,
            'response_size': response.content_length or 0,
        })
        
        # Add response headers (filtered)
        request_data['response_headers'] = self._filter_sensitive_data(dict(response.headers))
        
        # Add response body if enabled and successful
        if (self.log_response_body and 
            response.status_code < 400 and 
            response.content_length and 
            response.content_length < self.max_body_size):
            try:
                if response.is_json:
                    response_data = response.get_json()
                    request_data['response_body'] = self._filter_sensitive_data(response_data)
            except Exception as e:
                self.logger.warning(f"Failed to log response body: {e}")
        
        # Log the response
        log_level = self._get_log_level_for_status(response.status_code)
        self.request_logger.log(
            log_level, 
            "Request completed",
            extra={'request_data': request_data}
        )
        
        # Add correlation ID to response headers
        response.headers['X-Correlation-ID'] = g.correlation_id
        
        return response
    
    def _handle_exception(self, error: Exception) -> Any:
        """Handle exceptions during request processing."""
        correlation_id = getattr(g, 'correlation_id', 'unknown')
        
        # Calculate duration if available
        duration = None
        if hasattr(g, 'request_start_time'):
            duration = int((time.time() - g.request_start_time) * 1000)
        
        # Prepare error data
        error_data = {
            'correlation_id': correlation_id,
            'method': request.method,
            'path': request.path,
            'remote_addr': self._get_client_ip(),
            'user_id': self._get_user_id(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'duration': duration,
        }
        
        # Log the exception
        if isinstance(error, HTTPException):
            # HTTP exceptions (4xx, 5xx)
            error_data['status_code'] = error.code
            if error.code >= 500:
                self.logger.error(f"HTTP {error.code} error", extra=error_data, exc_info=True)
            else:
                self.logger.warning(f"HTTP {error.code} error", extra=error_data)
        else:
            # Unexpected exceptions
            error_data['status_code'] = 500
            self.logger.error("Unhandled exception", extra=error_data, exc_info=True)
        
        # Re-raise the exception to let Flask handle it
        raise error
    
    def _get_user_id(self) -> Optional[str]:
        """Get current user ID from JWT token."""
        try:
            return get_jwt_identity()
        except Exception:
            return None
    
    def _get_client_ip(self) -> str:
        """Get client IP address, considering proxy headers."""
        # Check for common proxy headers
        if request.headers.get('X-Forwarded-For'):
            return request.headers['X-Forwarded-For'].split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers['X-Real-IP']
        else:
            return request.remote_addr or 'unknown'
    
    def _filter_sensitive_data(self, data: Any) -> Any:
        """
        Filter sensitive data from logs.
        
        Args:
            data: Data to filter
            
        Returns:
            Filtered data with sensitive fields masked
        """
        if isinstance(data, dict):
            filtered = {}
            for key, value in data.items():
                key_lower = key.lower()
                if any(sensitive in key_lower for sensitive in self.SENSITIVE_FIELDS):
                    filtered[key] = '***FILTERED***'
                elif isinstance(value, (dict, list)):
                    filtered[key] = self._filter_sensitive_data(value)
                else:
                    filtered[key] = value
            return filtered
        elif isinstance(data, list):
            return [self._filter_sensitive_data(item) for item in data]
        else:
            return data
    
    def _get_log_level_for_status(self, status_code: int) -> int:
        """
        Get appropriate log level for HTTP status code.
        
        Args:
            status_code: HTTP status code
            
        Returns:
            Logging level constant
        """
        if status_code >= 500:
            return logging.ERROR
        elif status_code >= 400:
            return logging.WARNING
        else:
            return logging.INFO


def setup_request_logging(app: Flask, **kwargs) -> LoggingMiddleware:
    """
    Convenience function to setup request logging middleware.
    
    Args:
        app: Flask application
        **kwargs: Additional arguments for LoggingMiddleware
        
    Returns:
        Configured LoggingMiddleware instance
    """
    middleware = LoggingMiddleware(**kwargs)
    middleware.init_app(app)
    return middleware
