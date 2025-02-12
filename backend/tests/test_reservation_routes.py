from datetime import date
import pytest
from flask import Flask
from sqlalchemy import text
from routes.reservation_routes import reservation_bp
from database import engine, Base, SessionLocal
from models import Reservation, Room, Structure
# pylint: disable=all


@pytest.fixture(scope="module")
def app():
    app = Flask(__name__)
    app.config.from_object("config.TestConfig")
    app.register_blueprint(reservation_bp)
    Base.metadata.create_all(bind=engine)
    yield app
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def init_db():
    """Ensure a clean database before each test."""
    db = SessionLocal()
    db.execute(text("DROP VIEW IF EXISTS structure_reservations CASCADE;"))
    db.execute(text("TRUNCATE TABLE reservation RESTART IDENTITY CASCADE;"))
    db.execute(text("TRUNCATE TABLE room RESTART IDENTITY CASCADE;"))
    db.execute(text("TRUNCATE TABLE structure RESTART IDENTITY CASCADE;"))
    db.commit()

    # Create test structure
    structure = Structure(name="Test Structure", street="Test Street", city="Test City")
    db.add(structure)
    db.commit()
    db.refresh(structure)

    # Create test room
    room = Room(name="Test Room", capacity=2, id_structure=structure.id)
    db.add(room)
    db.commit()
    db.refresh(room)

    yield db  # Provide initialized DB to tests

    db.close()



def test_create_reservation(client, init_db):
    room = init_db.query(Room).first()
    response = client.post(
        "/api/v1/reservations",
        json={
            "reservationNumber": "RES12345",
            "startDate": "2025-02-10",
            "endDate": "2025-02-15",
            "roomName": room.name,
        },
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["reservation"]["reservationNumber"] == "RES12345"
    assert data["reservation"]["startDate"] == "2025-02-10"


def test_create_reservation_missing_fields(client):
    response = client.post(
        "/api/v1/reservations", json={"reservationNumber": "RES12345"}
    )
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_create_reservation_invalid_date(client, init_db):
    room = init_db.query(Room).first()
    response = client.post(
        "/api/v1/reservations",
        json={
            "reservationNumber": "RES12346",
            "startDate": "10-02-2025",
            "endDate": "15-02-2025",
            "roomName": room.name,
        },
    )
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_create_reservation_room_not_found(client):
    response = client.post(
        "/api/v1/reservations",
        json={
            "reservationNumber": "RES12347",
            "startDate": "2025-02-10",
            "endDate": "2025-02-15",
            "roomName": "NonExistentRoom",
        },
    )
    assert response.status_code == 404
    assert "error" in response.get_json()


def test_get_reservations(client):
    response = client.get("/api/v1/reservations")
    assert response.status_code == 200
    data = response.get_json()
    assert "reservations" in data


def test_get_reservation_per_month(client, init_db):
    structure = init_db.query(Structure).first()
    room = init_db.query(Room).first()

    reservations = [
        Reservation(id_reference="RES1001", start_date="2025-01-10", end_date="2025-01-15", id_room=room.id, status="Pending"),
        Reservation(id_reference="RES1002", start_date="2025-02-05", end_date="2025-02-10", id_room=room.id, status="Pending"),
    ]
    init_db.add_all(reservations)
    init_db.commit()

    response = client.get(f"/api/v1/reservations/monthly/{structure.id}")
    assert response.status_code == 200
    data = response.get_json()

    print("DEBUG API RESPONSE:", data)  # Add this for debugging

    # Check that only the inserted reservations exist
    expected_counts = {
        "January": 1,
        "February": 1,
        "March": 0,
        "April": 0,
        "May": 0,
        "June": 0,
        "July": 0,
        "August": 0,
        "September": 0,
        "October": 0,
        "November": 0,
        "December": 0,
    }

    for entry in data:
        assert entry["total_reservations"] == expected_counts[entry["month"]], f"Mismatch in {entry['month']}: {entry['total_reservations']}"
