import pytest
from flask import Flask
from routes.reservation_routes import reservation_bp
from models import Base, Room, Reservation  # Ensure Reservation model is imported if not already
from database import engine, SessionLocal
from datetime import datetime

@pytest.fixture(scope="module")
def setup_db():
    """Setup the database before tests and tear it down after."""
    # Create the Flask app and register the reservation blueprint
    app = Flask(__name__)
    app.config.from_object('config.TestConfig')  # Ensure test config is used
    app.register_blueprint(reservation_bp)

    # Create all tables in the database
    Base.metadata.create_all(bind=engine)

    # Create a test client for sending requests
    client = app.test_client()

    # Start a session to interact with the DB
    session = SessionLocal()

    # Add a room to the database to use in tests
    room = Room(name="Test Room", description="A test room")
    session.add(room)
    session.commit()

    # Yield client and session to be used in the tests
    yield client, session

    # Cleanup: Drop tables after all tests are complete
    Base.metadata.drop_all(bind=engine)
    session.close()


@pytest.fixture
def setup_reservation(setup_db):
    """Setup a reservation in the database for testing."""
    client, session = setup_db

    # Add a reservation to the database to use in tests
    room = session.query(Room).first()  # Fetch the room to associate with the reservation
    reservation = Reservation(
        reservationNumber="RES1234",
        startDate=datetime(2025, 3, 1),
        endDate=datetime(2025, 3, 5),
        room_id=room.id
    )
    session.add(reservation)
    session.commit()

    yield client, session, reservation  # Yield reservation info for tests


def test_create_reservation_success(setup_db):
    client, session = setup_db

    data = {
        "reservationNumber": "ABC123",
        "startDate": "2025-03-01",
        "endDate": "2025-03-05",
        "roomName": "Test Room"
    }

    # Make a POST request to create the reservation
    response = client.post('/api/v1/reservations', json=data)

    # Check that the response status code is 201 (created)
    assert response.status_code == 201

    # Check that the response contains the correct reservation data
    response_data = response.get_json()
    assert response_data['message'] == "Reservation created successfully"
    assert response_data['reservation']['reservationNumber'] == "ABC123"
    assert response_data['reservation']['roomName']['name'] == "Test Room"


def test_create_reservation_missing_fields(setup_db):
    client, session = setup_db

    data = {
        "reservationNumber": "ABC123",
        "startDate": "2025-03-01",
        # 'endDate' and 'roomName' are missing
    }

    response = client.post('/api/v1/reservations', json=data)

    # Check that the response status code is 400 (bad request)
    assert response.status_code == 400

    # Check that the error message is as expected
    response_data = response.get_json()
    assert response_data['error'] == "Missing required fields"


def test_create_reservation_invalid_date(setup_db):
    client, session = setup_db

    data = {
        "reservationNumber": "ABC123",
        "startDate": "2025-03-01",
        "endDate": "invalid-date",  # Invalid date format
        "roomName": "Test Room"
    }

    response = client.post('/api/v1/reservations', json=data)

    # Check that the response status code is 400 (bad request)
    assert response.status_code == 400

    # Check that the error message is as expected
    response_data = response.get_json()
    assert response_data['error'] == "Invalid date format. Use 'YYYY-MM-DD'"


def test_get_reservations(setup_db):
    client, session = setup_db

    # Create a reservation first
    reservation_data = {
        "reservationNumber": "DEF456",
        "startDate": "2025-03-01",
        "endDate": "2025-03-05",
        "roomName": "Test Room"
    }
    client.post('/api/v1/reservations', json=reservation_data)

    # Make a GET request to fetch all reservations
    response = client.get('/api/v1/reservations')

    # Check that the response status code is 200 (OK)
    assert response.status_code == 200

    # Check that the reservations are returned correctly
    response_data = response.get_json()
    assert "reservations" in response_data
    assert len(response_data['reservations']) == 1


def test_get_reservation_by_id(setup_reservation):
    client, session, reservation = setup_reservation

    # Make a GET request to fetch the reservation by ID
    response = client.get(f'/api/v1/reservations/{reservation.id}')

    # Check that the response status code is 200 (OK)
    assert response.status_code == 200

    # Check that the reservation data is returned correctly
    response_data = response.get_json()
    assert response_data['reservation']['reservationNumber'] == reservation.reservationNumber
    assert response_data['reservation']['roomName'] == "Test Room"


def test_create_reservation_invalid_room(setup_db):
    client, session = setup_db

    data = {
        "reservationNumber": "GHI7890",
        "startDate": "2025-04-01",
        "endDate": "2025-04-05",
        "roomName": "Nonexistent Room"  # This room doesn't exist
    }

    response = client.post('/api/v1/reservations', json=data)

    # Check that the response status code is 404 (not found)
    assert response.status_code == 404

    # Check that the error message is as expected
    response_data = response.get_json()
    assert response_data['error'] == "Room not found"


def test_delete_reservation(setup_reservation):
    client, session, reservation = setup_reservation

    # Make a DELETE request to remove the reservation
    response = client.delete(f'/api/v1/reservations/{reservation.id}')

    # Check that the response status code is 200 (OK)
    assert response.status_code == 200

    # Check that the message is as expected
    response_data = response.get_json()
    assert response_data['message'] == "Reservation deleted successfully"

    # Verify the reservation no longer exists
    response = client.get(f'/api/v1/reservations/{reservation.id}')
    assert response.status_code == 404
    response_data = response.get_json()
    assert response_data['error'] == "Reservation not found"
