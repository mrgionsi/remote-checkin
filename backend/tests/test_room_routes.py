import pytest
from flask import Flask
from routes.room_routes import room_bp
from database import engine, Base, SessionLocal
from models import Room, Structure

# pylint: disable=all

@pytest.fixture(scope="module")
def app():
    # Create the Flask app and configure it for testing
    """
    Create and configure a Flask application for testing.

    This fixture initializes a Flask application by loading the testing configuration from
    'config.TestConfig', registering the room blueprint, and creating all required tables
    in the test database. It yields the configured app instance for use in tests and, once
    testing is complete, drops all the tables to clean up the database.

    Yields:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__)
    app.config.from_object("config.TestConfig")  # Load testing config
    app.register_blueprint(room_bp)  # Register the room blueprint
    # Create all tables in the test database
    Base.metadata.create_all(bind=engine)
    yield app
    Base.metadata.drop_all(bind=engine)  # Drop tables after tests


@pytest.fixture
def client(app):
    # Use Flask's test client to simulate API requests
    """
    Return a test client for simulating API requests on a Flask application.

    This function creates and returns a test client for the provided Flask app using its
    built-in test_client() method. The returned client can be used to simulate HTTP requests
    during testing.

    Parameters:
        app (Flask): A Flask application instance configured for testing.

    Returns:
        FlaskClient: A test client instance for making simulated API requests.
    """
    return app.test_client()


@pytest.fixture
def init_db():
    # Initialize the database with some data for testing
    """
    Initialize the test database with a sample structure and a linked room for use in API testing.

    This function creates a new SQLAlchemy session, adds a test Structure (with preset name, street, and city)
    to the database, commits the change, and then creates a test Room associated with the newly added structure.
    It prints the created Room instance for debugging purposes. The function yields the active session so that
    tests can interact with the pre-populated database state. After the tests complete, the session is closed
    to ensure proper resource cleanup.

    Yields:
        Session: An active SQLAlchemy session containing the test Structure and Room.
    """
    db: SessionLocal = SessionLocal()

    # Add a test structure first so rooms can be linked to it
    structure = Structure(name="Test Structure", street="Test Street", city="Test City")
    db.add(structure)
    db.commit()
    db.refresh(structure)

    # Now add a room that links to the structure
    room = Room(name="Test Room", capacity=2, id_structure=structure.id)
    db.add(room)
    db.commit()
    db.refresh(room)
    print(room)
    # Yield the db session so it can be used in the tests
    yield db
    db.close()  # Clean up the database after tests


def test_add_room(client, init_db):
    # Get the latest structure ID from the test database
    """
    Test the POST /api/v1/rooms endpoint for adding a new room.

    This test retrieves the latest structure from the initialized database and uses its ID to
    construct a JSON payload for creating a new room. The payload includes the room name ("New Room"),
    its capacity (3), and the associated structure ID. After sending the POST request, the test asserts
    that the response has a status code of 201 (Created) and that the returned JSON matches the input data.

    Parameters:
        client (FlaskClient): A test client for issuing API requests to the Flask application.
        init_db (Session): A SQLAlchemy session fixture with the test database already populated with structures.

    Returns:
        None

    Raises:
        AssertionError: If the response status code is not 201 or the returned data does not match the expected values.
    """
    structure = init_db.query(Structure).order_by(Structure.id.desc()).first()

    # Test the POST /rooms endpoint to add a room
    response = client.post(
        "/api/v1/rooms",
        json={
            "name": "New Room",
            "capacity": 3,
            "id_structure": structure.id,  # Use the latest structure's ID
        },
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["name"] == "New Room"
    assert data["capacity"] == 3
    assert data["id_structure"] == structure.id


def test_get_rooms(client, init_db):
    # Test the GET /rooms endpoint to fetch rooms
    response = client.get("/api/v1/rooms")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) > 0  # Assuming there is at least one room in the test database


def test_get_room_by_id(client, init_db):
    # Test the GET /rooms/<id> endpoint
    room = init_db.query(Room).first()  # Get the first room from the test DB
    response = client.get(f"/api/v1/rooms/{room.id}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == room.id
    assert data["name"] == room.name


def test_delete_room(client, init_db):
    # Test the DELETE /rooms/<id> endpoint
    room = init_db.query(Room).first()  # Get the first room from the test DB
    response = client.delete(f"/api/v1/rooms/{room.id}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Room deleted successfully"

    # Try to fetch the room again and ensure it no longer exists
    response = client.get(f"/api/v1/rooms/{room.id}")
    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "Room not found"


def test_add_room_invalid_data(client):
    # Test the POST /rooms endpoint with invalid data
    # Missing required fields
    """
    Test the POST /api/v1/rooms endpoint with invalid data.

    This test sends a POST request with a JSON payload that omits required fields (specifically "name" and "id_structure").
    It verifies that the endpoint responds with a 400 Bad Request status code and that an error message is included in the JSON response.

    Parameters:
        client (FlaskClient): A Flask test client used to simulate HTTP requests.
    """
    response = client.post(
        "/api/v1/rooms",
        json={
            "capacity": 3,  # Missing "name" and "id_structure"
        },
    )
    assert response.status_code == 400  # Expecting a 400 Bad Request
    data = response.get_json()
    assert "error" in data  # Ensure there is an error message


def test_get_room_not_found(client):
    # Test the GET /rooms/<id> endpoint with a non-existent room ID
    response = client.get("/api/v1/rooms/99999")  # Assuming this ID doesn't exist
    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "Room not found"


def test_delete_room_not_found(client, init_db):
    # Test the DELETE /rooms/<id> endpoint with a non-existent room ID
    """
    Tests the DELETE /api/v1/rooms/<id> endpoint when attempting to delete a non-existent room.

    This test sends a DELETE request to the API with a room ID that is assumed not to exist (99999). It verifies that the API returns a 404 status code and that the error message in the JSON response is 'Room not found'.

    Parameters:
        client (FlaskClient): A test client fixture for making HTTP requests to the API.
        init_db: A fixture to initialize the database context for testing.

    Returns:
        None
    """
    response = client.delete("/api/v1/rooms/99999")  # Assuming this ID doesn't exist
    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "Room not found"


def test_get_rooms_empty(client, init_db):
    # Test the GET /rooms endpoint when there are no rooms
    # Delete all rooms from the DB for this test
    """
    Test the GET /api/v1/rooms endpoint when no rooms exist.

    This test function deletes all room records from the database and then sends a GET request to the /api/v1/rooms endpoint.
    It verifies that the endpoint returns an HTTP 200 status and that the response payload is an empty list.

    Parameters:
        client: A Flask test client fixture for simulating API requests.
        init_db: A fixture that initializes the database before the test.

    Raises:
        AssertionError: If the response status is not 200 or if the returned data is not an empty list.
    """
    db: SessionLocal = SessionLocal()
    db.query(Room).delete()
    db.commit()

    response = client.get("/api/v1/rooms")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 0  # Ensure no rooms are returned


def test_add_room_with_existing_id(client, init_db):
    # Test adding a room with an existing structure ID
    existing_structure_id = 1  # Assuming a structure with ID 1 exists
    response = client.post(
        "/api/v1/rooms",
        json={
            "name": "Another Room",
            "capacity": 4,
            "id_structure": existing_structure_id,
        },
    )
    assert response.status_code == 201  # Room should be created successfully
    data = response.get_json()
    assert data["name"] == "Another Room"
    assert data["capacity"] == 4
    assert data["id_structure"] == existing_structure_id
