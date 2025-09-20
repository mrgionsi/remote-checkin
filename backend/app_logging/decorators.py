"""
Logging decorators for function and route-level logging.

This module provides decorators for automatic function entry/exit logging,
performance monitoring, and route-specific logging.
"""

import time
import functools
import logging
from typing import Callable, Any, Optional, Dict, List
from flask import request, g

from .config import get_logger
from .utils import get_correlation_id, safe_extra_fields


def log_function(
    logger: Optional[logging.Logger] = None,
    level: int = logging.INFO,
    include_args: bool = True,
    include_result: bool = False,
    max_arg_length: int = 100
) -> Callable:
    """
    Decorator for automatic function entry/exit logging.
    
    Args:
        logger: Logger instance to use (defaults to function's module logger)
        level: Log level to use
        include_args: Whether to log function arguments
        include_result: Whether to log function return value
        max_arg_length: Maximum length of arguments to log
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        func_logger = logger or get_logger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            correlation_id = get_correlation_id()
            
            # Prepare function info
            func_info = {
                'function': f"{func.__module__}.{func.__qualname__}",
                'correlation_id': correlation_id
            }
            
            # Add arguments if requested
            if include_args:
                func_info['function_args'] = _format_args(args, max_arg_length)
                func_info['function_kwargs'] = _format_kwargs(kwargs, max_arg_length)
            
            # Log function entry
            func_logger.log(level, f"Entering function {func.__qualname__}", extra=safe_extra_fields(func_info))
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # Calculate execution time
                duration = int((time.time() - start_time) * 1000)  # milliseconds
                func_info['duration_ms'] = duration
                
                # Add result if requested
                if include_result:
                    func_info['result'] = _format_value(result, max_arg_length)
                
                # Log successful exit
                func_logger.log(level, f"Exiting function {func.__qualname__}", extra=func_info)
                
                return result
                
            except Exception as e:
                # Calculate execution time
                duration = int((time.time() - start_time) * 1000)  # milliseconds
                func_info['duration_ms'] = duration
                func_info['error'] = str(e)
                func_info['error_type'] = type(e).__name__
                
                # Log exception
                func_logger.error(f"Exception in function {func.__qualname__}", extra=func_info, exc_info=True)
                
                # Re-raise the exception
                raise
        
        return wrapper
    return decorator


def log_route(
    logger: Optional[logging.Logger] = None,
    level: int = logging.INFO,
    include_request_data: bool = True,
    include_response_data: bool = False
) -> Callable:
    """
    Decorator for route-specific logging with Flask request context.
    
    Args:
        logger: Logger instance to use
        level: Log level to use
        include_request_data: Whether to log request data
        include_response_data: Whether to log response data
        
    Returns:
        Decorated route function
    """
    def decorator(func: Callable) -> Callable:
        func_logger = logger or get_logger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            correlation_id = get_correlation_id()
            
            # Prepare route info
            route_info = _prepare_route_info(func, correlation_id, include_request_data)
            
            # Log route entry
            func_logger.log(level, f"Handling route {func.__qualname__}", extra=route_info)
            
            try:
                # Execute route function
                result = func(*args, **kwargs)
                
                # Log successful completion
                _log_route_success(func_logger, level, func, start_time, route_info, result, include_response_data)
                
                return result
                
            except Exception as e:
                # Log exception
                _log_route_error(func_logger, func, start_time, route_info, e)
                raise
        
        return wrapper
    return decorator


def log_performance(
    threshold_ms: int = 1000,
    logger: Optional[logging.Logger] = None,
    level: int = logging.WARNING
) -> Callable:
    """
    Decorator for performance monitoring and slow operation logging.
    
    Args:
        threshold_ms: Threshold in milliseconds for slow operation warning
        logger: Logger instance to use
        level: Log level for slow operations
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        func_logger = logger or get_logger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # Always log performance regardless of success/failure
                duration = int((time.time() - start_time) * 1000)  # milliseconds
                
                perf_info = {
                    'function': f"{func.__module__}.{func.__qualname__}",
                    'duration_ms': duration,
                    'correlation_id': get_correlation_id(),
                }
                
                if duration >= threshold_ms:
                    func_logger.log(
                        level,
                        f"Slow operation detected: {func.__qualname__} took {duration}ms",
                        extra=perf_info
                    )
                else:
                    func_logger.debug(
                        f"Performance: {func.__qualname__} took {duration}ms",
                        extra=perf_info
                    )
        
        return wrapper
    return decorator


def log_database_operation(
    operation_type: str,
    logger: Optional[logging.Logger] = None,
    level: int = logging.INFO
) -> Callable:
    """
    Decorator for database operation logging.
    
    Args:
        operation_type: Type of database operation (e.g., 'CREATE', 'READ', 'UPDATE', 'DELETE')
        logger: Logger instance to use
        level: Log level to use
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        func_logger = logger or get_logger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            correlation_id = get_correlation_id()
            
            db_info = {
                'operation_type': operation_type,
                'function': f"{func.__module__}.{func.__qualname__}",
                'correlation_id': correlation_id,
            }
            
            # Log operation start
            func_logger.log(level, f"Starting {operation_type} operation in {func.__qualname__}", extra=db_info)
            
            try:
                result = func(*args, **kwargs)
                
                # Calculate execution time
                duration = int((time.time() - start_time) * 1000)  # milliseconds
                db_info['duration_ms'] = duration
                
                # Log successful completion
                func_logger.log(level, f"{operation_type} operation completed successfully", extra=db_info)
                
                return result
                
            except Exception as e:
                # Calculate execution time
                duration = int((time.time() - start_time) * 1000)  # milliseconds
                db_info['duration_ms'] = duration
                db_info['error'] = str(e)
                db_info['error_type'] = type(e).__name__
                
                # Log database error
                func_logger.error(f"{operation_type} operation failed", extra=db_info, exc_info=True)
                
                # Re-raise the exception
                raise
        
        return wrapper
    return decorator


def _format_args(args: tuple, max_length: int) -> List[str]:
    """Format function arguments for logging."""
    return [_format_value(arg, max_length) for arg in args]


def _format_kwargs(kwargs: Dict[str, Any], max_length: int) -> Dict[str, str]:
    """Format function keyword arguments for logging."""
    return {key: _format_value(value, max_length) for key, value in kwargs.items()}


def _prepare_route_info(func: Callable, correlation_id: Optional[str], include_request_data: bool) -> Dict[str, Any]:
    """Prepare route information for logging."""
    from flask import request
    
    route_info = {
        'route_function': func.__qualname__,
        'correlation_id': correlation_id,
        'method': request.method,
        'path': request.path,
        'endpoint': request.endpoint,
    }
    
    if include_request_data:
        route_info.update({
            'remote_addr': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'query_params': dict(request.args),
        })
        
        # Add user ID if available
        try:
            from flask_jwt_extended import get_jwt_identity
            user_id = get_jwt_identity()
            if user_id:
                route_info['user_id'] = user_id
        except Exception:
            pass
    
    return route_info


def _log_route_success(func_logger: logging.Logger, level: int, func: Callable, 
                      start_time: float, route_info: Dict[str, Any], result: Any, 
                      include_response_data: bool) -> None:
    """Log successful route completion."""
    # Calculate execution time
    duration = int((time.time() - start_time) * 1000)  # milliseconds
    route_info['duration_ms'] = duration
    
    # Add response data if requested
    if include_response_data and hasattr(result, 'status_code'):
        route_info['status_code'] = result.status_code
    
    # Log successful completion
    func_logger.log(level, f"Route {func.__qualname__} completed successfully", extra=route_info)


def _log_route_error(func_logger: logging.Logger, func: Callable, 
                    start_time: float, route_info: Dict[str, Any], error: Exception) -> None:
    """Log route error."""
    # Calculate execution time
    duration = int((time.time() - start_time) * 1000)  # milliseconds
    route_info['duration_ms'] = duration
    route_info['error'] = str(error)
    route_info['error_type'] = type(error).__name__
    
    # Log exception
    func_logger.error(f"Exception in route {func.__qualname__}", extra=route_info, exc_info=True)


def _format_value(value: Any, max_length: int) -> str:
    """Format a value for logging with length limit."""
    try:
        str_value = str(value)
        if len(str_value) > max_length:
            return str_value[:max_length] + "..."
        return str_value
    except Exception:
        return f"<{type(value).__name__}>"
