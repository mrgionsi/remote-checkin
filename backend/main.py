"""
Main module for the remote check-in system.

This module initializes the Flask app, sets up database tables,
and registers blueprints for routing.
"""
# pylint: disable=C0303,E0401
import os
import re
from flask_jwt_extended import JWTManager
from flask import Flask
from flask_cors import CORS
from routes.admin_routes import admin_bp
from routes.room_routes import room_bp
from routes.reservation_routes import reservation_bp
from routes.upload_reservation_routes import upload_bp
from routes.client_reservation_routes import client_reservation_bp

app = Flask(__name__)

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

allowed_origins = os.getenv("ALLOWED_CORS", "http://localhost:4200").split(",")

CORS(
    app,
    origins=allowed_origins,
    supports_credentials=True,
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type", "Authorization"],
)

# Create database tables
# Base.metadata.create_all(bind=engine)

# Register blueprints
app.register_blueprint(admin_bp)
app.register_blueprint(room_bp)
app.register_blueprint(reservation_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(client_reservation_bp)


@app.route("/")
def home():
    """
    Home route that returns a simple greeting message.

    This route is used to check if the server is running.
    """
    return "Hello, Flask!"


if __name__ == "__main__":
    app.run(debug=True)
