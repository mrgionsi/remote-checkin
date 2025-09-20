"""
Utility functions for the logging system.

This module contains utility functions that are shared across
the logging components to avoid circular imports.
"""

from typing import Optional, Dict, Any


def get_correlation_id() -> Optional[str]:
    """
    Get the current correlation ID from Flask's g object.
    
    Returns:
        Correlation ID if available, None otherwise
    """
    try:
        from flask import g
        return getattr(g, 'correlation_id', None)
    except (ImportError, RuntimeError):
        # Outside Flask context
        return None


def safe_extra_fields(extra_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter out reserved field names from extra logging data to prevent KeyError.
    
    Args:
        extra_data: Dictionary of extra fields for logging
        
    Returns:
        Filtered dictionary with reserved fields removed
    """
    # Reserved field names that conflict with Python's logging system
    reserved_fields = {
        'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
        'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
        'thread', 'threadName', 'processName', 'process', 'exc_info', 'exc_text',
        'stack_info', 'getMessage', 'taskName', 'asctime', 'message'
    }
    
    return {
        key: value for key, value in extra_data.items() 
        if key not in reserved_fields and not key.startswith('_')
    }
