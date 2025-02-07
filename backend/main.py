from flask import Flask, request, jsonify
from datetime import datetime
from flask_cors import CORS
from database import SessionLocal
from models import Reservation, ClientReservations, Room, Client

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

    # Validate required fields
    required_fields = ['reservationNumber', 'startDate', 'endDate', 'roomName']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    session = SessionLocal()

    try:
        # Validate and parse date fields
        start_date = datetime.strptime(data['startDate'], '%Y-%m-%d')
        end_date = datetime.strptime(data['endDate'], '%Y-%m-%d')

        # Find room ID by name
        room = session.query(Room).filter(Room.name == data['roomName']).first()
        print(room)
        if not room:
            return jsonify({"error": "Room not found"}), 404

        # Check if client exists
        """ client = session.query(Client).filter(Client.id == data['clientId']).first()
        if not client:
            return jsonify({"error": "Client not found"}), 404 """

        # Create a new reservation entry
        new_reservation = Reservation(
            id_reference=data['reservationNumber'],
            start_date=start_date,
            end_date=end_date,
            id_room=room.id
        )
        
        session.add(new_reservation)
        session.flush()  # Generate reservation ID

        # Link client to reservation
        """ client_reservation = ClientReservations(
            id_reservation=new_reservation.id,
            id_client=client.id
        )
        session.add(client_reservation) """

        # Commit transaction
        session.commit()

        return jsonify({
            "message": "Reservation created successfully",
            "reservation": {
                "id": new_reservation.id,
                "reservationNumber": new_reservation.id_reference,
                "startDate": new_reservation.start_date.strftime('%Y-%m-%d'),
                "endDate": new_reservation.end_date.strftime('%Y-%m-%d'),
                "roomName": new_reservation.room.to_dict()
            }
        }), 201

    except ValueError:
        session.rollback()
        return jsonify({"error": "Invalid date format. Use 'YYYY-MM-DD'"}), 400
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

# GET endpoint to view all reservations (for testing purposes)
@app.route('/api/v1/reservations', methods=['GET'])
def get_reservations():
    return jsonify({"reservations": reservations.to_dict()})

if __name__ == '__main__':
    app.run(debug=True)