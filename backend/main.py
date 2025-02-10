# main.py

from flask import Flask
from flask_cors import CORS
from database import engine, Base
from routes.room_routes import room_bp
from routes.reservation_routes import reservation_bp  # Import the new reservation blueprint

app = Flask(__name__)
CORS(app, origins="http://localhost:4200")  # Change this to match your frontend URL

# Create database tables
Base.metadata.create_all(bind=engine)

# Register blueprints
app.register_blueprint(room_bp)
app.register_blueprint(reservation_bp)  # Register the reservation blueprint

@app.route('/')
def home():
    return "Hello, Flask!"

if __name__ == '__main__':
    app.run(debug=True)
