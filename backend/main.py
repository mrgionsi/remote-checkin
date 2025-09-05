"""
Main module for the remote check-in system.

This module initializes the Flask app, sets up database tables,
and registers blueprints for routing.
"""
# pylint: disable=C0303,E0401
import os
import re
from flask_jwt_extended import JWTManager
from flask import Flask, make_response, request
from flask_cors import CORS
from routes.email_config_routes import email_config_bp
from routes.admin_routes import admin_bp
from routes.room_routes import room_bp
from routes.reservation_routes import reservation_bp
from routes.upload_reservation_routes import upload_bp
from routes.client_reservation_routes import client_reservation_bp
from flask_mail import Mail
from config import Config

app = Flask(__name__)

# Load configuration
app.config.from_object(Config())

# --- JWT Secret Key Handling and Security Configuration ---
jwt_secret_key = os.getenv("JWT_SECRET_KEY")
if not jwt_secret_key:
    raise RuntimeError(
        "JWT_SECRET_KEY environment variable is not set. Please set a strong secret key "
        "for production."
    )

# Enforce minimum length and complexity (at least 16 chars, with letters and numbers/symbols)
if (
    len(jwt_secret_key) < 16
    or not re.search(r"[A-Za-z]", jwt_secret_key)
    or not re.search(r"[\d\W]", jwt_secret_key)
):
    raise RuntimeError(
        "JWT_SECRET_KEY must be at least 16 characters long and contain both letters and "
        "numbers/symbols."
    )

app.config["JWT_SECRET_KEY"] = jwt_secret_key
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600  # 1 hour (in seconds)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = 60 * 60 * 24 * 30  # 30 days (in seconds)
app.config["JWT_ALGORITHM"] = "HS256"

jwt = JWTManager(app)

# Initialize Flask-Mail after all configuration is set
mail = Mail(app)
# Ensure mail is properly registered with app extensions
app.extensions['mail'] = mail

allowed_origins = os.getenv("ALLOWED_CORS", "http://localhost:4200").split(",")

CORS(
    app,
    origins=allowed_origins,
    supports_credentials=True,
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["Content-Type", "Authorization"],
    max_age=3600,  # Cache preflight response for 1 hour
)

# Create database tables
# Base.metadata.create_all(bind=engine)

# Register blueprints
app.register_blueprint(admin_bp)
app.register_blueprint(room_bp)
app.register_blueprint(reservation_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(client_reservation_bp)
app.register_blueprint(email_config_bp)

@app.route("/")
def home():
    """
    Home route that returns a simple greeting message.

    This route is used to check if the server is running.
    """
    return "Hello, Flask!"

@app.before_request
def handle_preflight():
    """
    Return an empty permissive CORS preflight response when the incoming request is an OPTIONS preflight.
    
    This function is intended to be used as a Flask `before_request` handler. If the request method is OPTIONS it returns an empty response with
    Access-Control-Allow-Origin, Access-Control-Allow-Headers, and Access-Control-Allow-Methods set to "*" to satisfy CORS preflight checks. For non-OPTIONS requests it does nothing (continues normal request handling).
    """
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

@app.route("/test-email-config")
def test_email_config():
    """
    Return JSON indicating whether Flask-Mail is configured and available.
    
    Checks the application's extensions for the 'mail' extension and returns a JSON-serializable
    dictionary describing the result.
    
    Returns:
    	A dict with at least the following keys:
    		- "status" (str): "success" if the mail extension is present, otherwise "error".
    		- "message" (str): Human-readable description of the outcome.
    	If the mail extension is present, the response also includes:
    		- "mail_type" (str): The Python type of the mail extension as a string.
    		- "extensions" (list): List of currently registered extension names (app.extensions keys).
    	On unexpected failures, returns an error dictionary with the exception message.
    """
    try:
        if 'mail' not in app.extensions:
            return {"status": "error", "message": "Flask-Mail extension not found"}

        mail = app.extensions['mail']
        return {
            "status": "success",
            "message": "Email configuration is available",
            "mail_type": str(type(mail)),
            "extensions": list(app.extensions.keys())
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    app.run(debug=True)
