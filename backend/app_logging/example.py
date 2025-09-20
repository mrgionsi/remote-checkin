#pylint: disable=C0301,C0413,W0718,C0301,E0401,C0415,R1720,R1705
"""
Example usage of the logging system for the remote check-in application.

This file demonstrates how to use various logging features including:
- Basic logging setup
- Decorators for automatic logging
- Manual logging with context
- Error handling with logging
"""

from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, create_access_token

# Import our logging components
from app_logging.config import setup_logging, get_logger
from app_logging.middleware import setup_request_logging
from app_logging.decorators import log_route, log_function, log_database_operation, log_performance

# Setup Flask app
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'demo-secret-key'
jwt = JWTManager(app)

# Setup logging system
setup_logging('logging-demo')

# Setup request middleware
setup_request_logging(
    app,
    exclude_paths=['/health'],
    log_request_body=True,
    log_response_body=False,
    max_body_size=1024
)

# Get logger for this module
logger = get_logger(__name__)


# Example 1: Basic route with logging decorator
@app.route('/api/demo/basic', methods=['GET'])
@log_route(include_request_data=True)
def basic_demo():
    """Demonstrate basic route logging."""
    logger.info("Processing basic demo request")
    return jsonify({"message": "Basic logging demo", "status": "success"})


# Example 2: Database operation simulation
@app.route('/api/demo/database', methods=['POST'])
@jwt_required()
@log_route(include_request_data=True)
@log_database_operation("CREATE")
def database_demo():
    """Demonstrate database operation logging."""
    data = request.get_json()

    logger.info("Creating new record", extra={
        'record_type': data.get('type', 'unknown'),
        'user_input': data.get('name', 'unnamed')
    })

    # Simulate database operation
    record_id = simulate_database_create(data)

    logger.info("Record created successfully", extra={
        'record_id': record_id,
        'operation_result': 'success'
    })

    return jsonify({
        "message": "Record created",
        "id": record_id,
        "status": "success"
    }), 201


# Example 3: Function with automatic logging
@log_function(include_args=True, include_result=True)
def simulate_database_create(data):
    """Simulate a database create operation."""
    import time
    import random

    # Simulate processing time
    time.sleep(0.1)

    # Generate mock ID
    record_id = random.randint(1000, 9999)

    logger.debug("Database simulation completed", extra={
        'generated_id': record_id,
        'input_data_keys': list(data.keys()) if data else []
    })

    return record_id


# Example 4: Performance monitoring
@app.route('/api/demo/slow', methods=['GET'])
@log_route()
@log_performance(threshold_ms=500)
def slow_operation_demo():
    """Demonstrate performance logging for slow operations."""
    import time

    logger.info("Starting slow operation")

    # Simulate slow operation
    time.sleep(0.8)  # This will trigger the performance warning

    logger.info("Slow operation completed")

    return jsonify({"message": "Slow operation completed", "duration": "800ms"})


# Example 5: Error handling with logging
@app.route('/api/demo/error', methods=['GET'])
@log_route(include_request_data=True)
def error_demo():
    """Demonstrate error logging."""
    error_type = request.args.get('type', 'generic')

    logger.info("Processing error demo", extra={
        'requested_error_type': error_type
    })

    try:
        if error_type == 'validation':
            raise ValueError("Invalid input data provided")
        elif error_type == 'database':
            raise ConnectionError("Database connection failed")
        elif error_type == 'permission':
            raise PermissionError("Insufficient permissions")
        else:
            raise RuntimeError("Generic error occurred")

    except ValueError as e:
        logger.warning("Validation error occurred", extra={
            'error_type': 'validation',
            'error_details': str(e),
            'user_input': error_type
        })
        return jsonify({"error": "Validation failed", "message": str(e)}), 400

    except (ConnectionError, PermissionError) as e:
        logger.error("System error occurred", extra={
            'error_type': type(e).__name__,
            'error_details': str(e),
            'requires_attention': True
        }, exc_info=True)
        return jsonify({"error": "System error", "message": "Please try again later"}), 500

    except Exception as e:
        logger.critical("Unexpected error occurred", extra={
            'error_type': 'unexpected',
            'error_details': str(e),
            'requires_immediate_attention': True
        }, exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


# Example 6: Authentication demo
@app.route('/api/demo/login', methods=['POST'])
@log_route(include_request_data=True)
def login_demo():
    """Demonstrate authentication logging."""
    data = request.get_json()
    username = data.get('username')

    logger.info("Login attempt", extra={
        'username': username,
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', '')
    })

    # Simulate authentication
    if username and len(username) > 3:
        # Successful login
        access_token = create_access_token(identity=username)

        logger.info("Login successful", extra={
            'username': username,
            'login_result': 'success',
            'token_created': True
        })

        return jsonify({
            'access_token': access_token,
            'message': 'Login successful'
        })
    else:
        # Failed login
        logger.warning("Login failed", extra={
            'username': username,
            'login_result': 'failed',
            'failure_reason': 'invalid_credentials'
        })

        return jsonify({'error': 'Invalid credentials'}), 401


# Example 7: Health check (excluded from detailed logging)
@app.route('/health')
def health_check():
    """Health check endpoint (excluded from detailed logging)."""
    return jsonify({"status": "healthy", "service": "logging-demo"})


# Example 8: Manual context logging
@app.route('/api/demo/context', methods=['POST'])
@log_route()
def context_demo():
    """Demonstrate manual logging with rich context."""
    data = request.get_json()

    # Create rich context for logging
    context = {
        'operation': 'context_demo',
        'request_size': len(str(data)) if data else 0,
        'has_nested_data': isinstance(data, dict) and any(isinstance(v, (dict, list)) for v in data.values()) if data else False,
        'client_info': {
            'ip': request.remote_addr,
            'user_agent_short': request.headers.get('User-Agent', '')[:50] + '...' if len(request.headers.get('User-Agent', '')) > 50 else request.headers.get('User-Agent', ''),
            'content_type': request.content_type
        }
    }

    logger.info("Processing context demo with rich information", extra=context)

    # Simulate some processing
    result = {
        'processed_keys': list(data.keys()) if isinstance(data, dict) else [],
        'processing_result': 'success',
        'timestamp': '2024-01-15T10:30:00Z'
    }

    logger.info("Context demo completed", extra={
        **context,
        'result_keys': list(result.keys()),
        'processing_duration': '50ms'
    })

    return jsonify(result)


if __name__ == '__main__':
    logger.info("Starting logging demo application")

    print("\n" + "="*60)
    print("LOGGING SYSTEM DEMO")
    print("="*60)
    print("Available endpoints:")
    print("  GET  /health                    - Health check (minimal logging)")
    print("  GET  /api/demo/basic            - Basic logging demo")
    print("  POST /api/demo/database         - Database operation logging")
    print("  GET  /api/demo/slow             - Performance monitoring demo")
    print("  GET  /api/demo/error?type=X     - Error handling demo")
    print("  POST /api/demo/login            - Authentication logging")
    print("  POST /api/demo/context          - Rich context logging")
    print("\nExample requests:")
    print("  curl http://localhost:5000/api/demo/basic")
    print("  curl -X POST http://localhost:5000/api/demo/login -H 'Content-Type: application/json' -d '{\"username\":\"demo\"}'")
    print("  curl http://localhost:5000/api/demo/error?type=validation")
    print("="*60)

    app.run(debug=True, port=5000)
