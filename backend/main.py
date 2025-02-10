from flask import Flask, request, jsonify
from datetime import datetime
from flask_cors import CORS
from database import engine, Base, SessionLocal
from routes.room_routes import room_bp
from models import Reservation, ClientReservations, Room, Client

app = Flask(__name__)
CORS(app, origins="http://localhost:4200")  # Change this to match your frontend URL

# Simulating an in-memory "database"
reservations = []

@app.route('/')
def home():
    return "Hello, Flask!"

@app.route('/api/v1/reservations', methods=['POST'])
def create_reservation():
    # Get the JSON payload from the request
    """
    Create a new reservation from the JSON payload of a POST request.
    
    This function extracts reservation details from the incoming JSON payload, validates the presence of
    required fields ("reservationNumber", "startDate", "endDate", "roomName"), and parses the date strings
    into datetime objects. It then queries the database to locate the room by its name. If the room is found,
    a new reservation is created and added to the database. The function commits the transaction and returns
    a JSON response with the reservation details and a 201 status code. If any validation fails (e.g., missing
    fields, invalid date formats) or if the room cannot be found, an appropriate error message with a relevant
    HTTP status code (400, 404, or 500) is returned. The function ensures that the database session is properly
    closed after the operation, rolling back the transaction in case of errors.
    
    Returns:
        A Flask JSON response containing:
            - On success (status 201): A message indicating the reservation was created successfully along with
              a dictionary of reservation details including the reservation ID, reservationNumber, startDate,
              endDate, and room information.
            - On failure (status 400, 404, or 500): A dictionary with an error message explaining the failure.
            
    Side Effects:
        - Adds a new reservation record to the database.
        - Commits the transaction, generating a new reservation ID.
        - Prints the room object for debugging purposes.
        
    Note:
        Client association functionality is commented out and may be implemented in a future update.
    """
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
    """
    Return a JSON response with all room reservations.
    
    This function retrieves all reservations and returns them in a JSON format. The reservations are expected to support
    conversion to a dictionary via the to_dict() method, and the resulting dictionary is returned under the key "reservations".
    
    Returns:
        flask.Response: A JSON response object containing the reservations in a dictionary format.
    """
    return jsonify({"reservations": reservations.to_dict()})


# Create database tables
Base.metadata.create_all(bind=engine)

# Register blueprints
app.register_blueprint(room_bp)

if __name__ == '__main__':
    app.run(debug=True)