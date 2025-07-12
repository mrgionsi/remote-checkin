"""
Main module for the remote check-in system.

This module initializes the Flask app, sets up database tables,
and registers blueprints for routing.
"""
#pylint: disable=C0303,E0401
import os
from flask_jwt_extended import JWTManager
from flask import Flask
from flask_cors import CORS
from routes.admin_routes import admin_bp
from routes.room_routes import room_bp
from routes.reservation_routes import reservation_bp  # Adjust the path as needed
from routes.upload_reservation_routes import upload_bp  # Adjust the path as needed
from routes.client_reservation_routes import client_reservation_bp  # Adjust the path as needed


app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")  # Cambia questa chiave in produzione!
jwt = JWTManager(app)
allowed_origins = os.getenv("ALLOWED_CORS", "http://localhost:4200").split(",")
CORS(app,
     origins=allowed_origins,
     supports_credentials=True,
     methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
     allow_headers=["Content-Type", "Authorization"],
     expose_headers=["Content-Type", "Authorization"])

# Create database tables
#Base.metadata.create_all(bind=engine)

# Register blueprints
app.register_blueprint(admin_bp)  # Register the admin blueprint
app.register_blueprint(room_bp)
app.register_blueprint(reservation_bp)  # Register the reservation blueprint
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
