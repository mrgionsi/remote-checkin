from flask import Flask, request, jsonify
from datetime import datetime
from flask_cors import CORS
from database import engine, Base
from routes.room_routes import room_bp
app = Flask(__name__)
CORS(app)

# Simulating an in-memory "database"
reservations = []

@app.route('/')
def home():
    return "Hello, Flask!"

@app.route('/api/v1/reservations', methods=['POST'])
def create_reservation():
    # Get the JSON payload from the request
    data = request.get_json()

    # Validate if required fields are in the payload
    if not data or not data.get('reservationNumber') or not data.get('startDate') or not data.get('endDate') or not data.get('roomName'):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # Validate and parse the date fields
        start_date = datetime.strptime(data['startDate'], '%Y-%m-%d')
        end_date = datetime.strptime(data['endDate'], '%Y-%m-%d')

        # Create a new reservation object (you can save this into a real database)
        reservation = {
            "reservationNumber": data['reservationNumber'],
            "startDate": start_date,
            "endDate": end_date,
            "roomName": data['roomName']
        }

        # Add the reservation to the simulated in-memory "database"
        reservations.append(reservation)

        return jsonify({"message": "Reservation created successfully", "reservation": reservation}), 201

    except ValueError as e:
        return jsonify({"error": "Invalid date format. Use 'YYYY-MM-DD'"}), 400

# GET endpoint to view all reservations (for testing purposes)
@app.route('/api/v1/reservations', methods=['GET'])
def get_reservations():
    return jsonify({"reservations": reservations})


# Create database tables
Base.metadata.create_all(bind=engine)

# Register blueprints
app.register_blueprint(room_bp)

if __name__ == '__main__':
    app.run(debug=True)