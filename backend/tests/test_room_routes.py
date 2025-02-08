import pytest
from flask import Flask
from routes.room_routes import room_bp
from database import engine, Base, SessionLocal
from models import Room, Structure

@pytest.fixture(scope="module")
def app():
    # Create the Flask app and configure it for testing
    app = Flask(__name__)
    app.config.from_object('config.TestConfig')  # Load testing config
    app.register_blueprint(room_bp)  # Register the room blueprint
    # Create all tables in the test database
    Base.metadata.create_all(bind=engine)
    yield app
    Base.metadata.drop_all(bind=engine)  # Drop tables after tests

@pytest.fixture
def client(app):
    # Use Flask's test client to simulate API requests
    return app.test_client()

@pytest.fixture
def init_db():
    # Initialize the database with some data for testing
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
    structure = init_db.query(Structure).order_by(Structure.id.desc()).first()

    # Test the POST /rooms endpoint to add a room
    response = client.post("/api/v1/rooms", json={
        "name": "New Room",
        "capacity": 3,
        "id_structure": structure.id  # Use the latest structure's ID
    })

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
    response = client.post("/api/v1/rooms", json={
        "capacity": 3,  # Missing "name" and "id_structure"
    })
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
    response = client.delete("/api/v1/rooms/99999")  # Assuming this ID doesn't exist
    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "Room not found"


def test_get_rooms_empty(client, init_db):
    # Test the GET /rooms endpoint when there are no rooms
    # Delete all rooms from the DB for this test
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
    response = client.post("/api/v1/rooms", json={
        "name": "Another Room",
        "capacity": 4,
        "id_structure": existing_structure_id
    })
    assert response.status_code == 201  # Room should be created successfully
    data = response.get_json()
    assert data["name"] == "Another Room"
    assert data["capacity"] == 4
    assert data["id_structure"] == existing_structure_id
