from datetime import datetime
import pytest
from flask import Flask
from sqlalchemy import text
from routes.reservation_routes import reservation_bp
from database import engine, Base, SessionLocal
from models import AdminStructure, Client, ClientReservations, Reservation, Role, Room, Structure, User
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
    """Ensure a clean database before each test by removing existing data."""
    db = SessionLocal()
    db.execute(text('DROP VIEW IF EXISTS structure_reservations;'))  # Use CASCADE to remove dependent objects

    # Remove data from dependent tables first
    db.query(AdminStructure).delete()
    db.query(User).delete()
    db.query(ClientReservations).delete()
    db.query(Reservation).delete()
    db.query(Room).delete()
    # Remove data from base tables
    db.query(Structure).delete()
    db.query(Client).delete()
    db.query(Role).delete()

    db.commit()


    # Create a test structure
    structure = Structure(id='1',name="Test Structure", street="Test Street", city="Test City")
    db.add(structure)
    db.commit()
    db.flush()
    db.refresh(structure)

    # Create a test room
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



def test_get_reservations_per_month_basic(client, init_db):
    """Test normal reservation retrieval per month."""
    db = init_db
    structure_id = db.query(Structure).first().id

    # Add reservations for different months
    room = db.query(Room).first()
    reservation1 = Reservation(
        id_reference="RES1", start_date=datetime(2024, 1, 10), end_date=datetime(2024, 1, 15), id_room=room.id
    )
    reservation2 = Reservation(
        id_reference="RES2", start_date=datetime(2024, 2, 5), end_date=datetime(2024, 2, 10), id_room=room.id
    )

    db.add_all([reservation1, reservation2])
    db.commit()

    response = client.get(f"/api/v1/reservations/monthly/{structure_id}")

    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 12  # 12 months
    assert any(item['month'] == 'January' and item['total_reservations'] == 1 for item in data)
    assert any(item['month'] == 'February' and item['total_reservations'] == 1 for item in data)


def test_get_reservations_per_month_no_reservations(client, init_db):
    """Test the scenario where there are no reservations for the structure."""
    db = init_db
    structure_id = db.query(Structure).first().id

    response = client.get(f"/api/v1/reservations/monthly/{structure_id}")

    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 12  # 12 months
    assert all(item['total_reservations'] == 0 for item in data)


def test_get_reservations_per_month_invalid_structure_id(client, init_db):
    """Test the scenario where an invalid structure_id is provided."""
    invalid_structure_id = 9999  # Assuming this structure ID doesn't exist

    response = client.get(f"/api/v1/reservations/monthly/{invalid_structure_id}")

    assert response.status_code == 404
    data = response.get_json()
    assert data["message"] == "Structure not found"  # Ensure the message matches the error returned

    """Test when no reservations exist for a structure."""
    """ _, structure_id = init_db  # DB is clean from fixture """

    response = client.get("/api/v1/reservations/monthly/1")
    assert response.status_code == 200

    data = response.get_json()
    assert len(data) == 12  # 12 months
    assert all(month["total_reservations"] == 0 for month in data)  # No reservations, so all months should be 0
