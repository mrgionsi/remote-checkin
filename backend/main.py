"""
Main module for the remote check-in system.

This module initializes the Flask app, sets up database tables,
and registers blueprints for routing.
"""
#pylint: disable=C0303,E0401

from flask import Flask
from flask_cors import CORS
from routes.room_routes import room_bp
from routes.reservation_routes import reservation_bp  # Adjust the path as needed


app = Flask(__name__)
CORS(app, origins="http://localhost:4200")  # Change this to match your frontend URL

# Create database tables
#Base.metadata.create_all(bind=engine)

# Register blueprints
app.register_blueprint(room_bp)
app.register_blueprint(reservation_bp)  # Register the reservation blueprint


@app.route("/")
def home():
    """
    Home route that returns a simple greeting message.

    This route is used to check if the server is running.
    """
    return "Hello, Flask!"


if __name__ == "__main__":
    app.run(debug=True)
