import pytest
from flask import Flask
from routes.reservation_routes import reservation_bp
from database import engine, Base, SessionLocal
from models import Room, Structure, Reservation
from datetime import datetime

@pytest.fixture(scope="module")
def app():
    app = Flask(__name__)
    app.config.from_object('config.TestConfig')
    app.register_blueprint(reservation_bp)
    Base.metadata.create_all(bind=engine)
    yield app
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def init_db():
    db = SessionLocal()
    structure = Structure(name="Test Structure", street="Test Street", city="Test City")
    db.add(structure)
    db.commit()
    db.refresh(structure)

    room = Room(name="Test Room", capacity=2, id_structure=structure.id)
    db.add(room)
    db.commit()
    db.refresh(room)
    yield db
    db.close()

def test_create_reservation(client, init_db):
    room = init_db.query(Room).first()
    response = client.post("/api/v1/reservations", json={
        "reservationNumber": "RES12345",
        "startDate": "2025-02-10",
        "endDate": "2025-02-15",
        "roomName": room.name
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data["reservation"]["reservationNumber"] == "RES12345"
    assert data["reservation"]["startDate"] == "2025-02-10"

def test_create_reservation_missing_fields(client):
    response = client.post("/api/v1/reservations", json={"reservationNumber": "RES12345"})
    assert response.status_code == 400
    assert "error" in response.get_json()

def test_create_reservation_invalid_date(client, init_db):
    room = init_db.query(Room).first()
    response = client.post("/api/v1/reservations", json={
        "reservationNumber": "RES12346",
        "startDate": "10-02-2025",
        "endDate": "15-02-2025",
        "roomName": room.name
    })
    assert response.status_code == 400
    assert "error" in response.get_json()

def test_create_reservation_room_not_found(client):
    response = client.post("/api/v1/reservations", json={
        "reservationNumber": "RES12347",
        "startDate": "2025-02-10",
        "endDate": "2025-02-15",
        "roomName": "NonExistentRoom"
    })
    assert response.status_code == 404
    assert "error" in response.get_json()

def test_get_reservations(client):
    response = client.get("/api/v1/reservations")
    assert response.status_code == 200
    data = response.get_json()
    assert "reservations" in data