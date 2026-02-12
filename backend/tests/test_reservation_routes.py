from datetime import datetime
import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from sqlalchemy import text
from routes.reservation_routes import reservation_bp
from database import engine, Base, SessionLocal
from models import AdminStructure, Client, ClientReservations, Reservation, Role, Room, Structure, User
# pylint: disable=all


@pytest.fixture(scope="module")
def app():
    app = Flask(__name__)
    app.config.from_object("config.TestConfig")
    app.config["JWT_SECRET_KEY"] = "test-secret"
    JWTManager(app)
    app.register_blueprint(reservation_bp)
    Base.metadata.create_all(bind=engine)
    yield app
    with engine.connect() as conn:
        try:
            conn.execute(text("DROP VIEW IF EXISTS structure_reservations CASCADE"))
        except Exception:
            pass
        try:
            conn.execute(text("DROP TABLE IF EXISTS structure_reservations CASCADE"))
        except Exception:
            pass
        conn.commit()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def init_db():
    """
    Prepare and provide a clean test database session.
    
    This fixture-like helper clears relevant tables and a view, commits the empty state, then seeds a test Structure (id "1") and a Room ("Test Room") linked to that Structure. It yields an active SQLAlchemy Session for use by tests and closes the session after the caller finishes.
    
    Side effects:
    - Drops the `structure_reservations` view if it exists.
    - Deletes rows from AdminStructure, User, ClientReservations, Reservation, Room, Structure, Client, and Role.
    - Inserts a Structure with id "1" and a Room named "Test Room".
    
    Yields:
        sqlalchemy.orm.Session: An initialized session connected to the cleaned and seeded test database.
    """
    db = SessionLocal()
    try:
        db.execute(text('DROP VIEW IF EXISTS structure_reservations CASCADE;'))
    except Exception:
        db.rollback()
        db.execute(text('DROP TABLE IF EXISTS structure_reservations CASCADE;'))

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


    role = Role(name="administrator")
    db.add(role)
    db.commit()
    db.refresh(role)

    user = User(
        username="testadmin",
        password="hashed",
        id_role=role.id,
        name="Test",
        surname="Admin",
        email="admin@example.com",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create a test structure
    structure = Structure(id='1', name="Test Structure", street="Test Street", city="Test City")
    db.add(structure)
    db.commit()
    db.flush()
    db.refresh(structure)

    # Create a test room
    room = Room(name="Test Room", capacity=2, id_structure=structure.id)
    db.add(room)
    db.commit()
    db.refresh(room)

    db.add(AdminStructure(id_user=user.id, id_structure=structure.id))
    db.commit()

    yield db  # Provide initialized DB to tests

    db.close()


@pytest.fixture
def auth_headers(app, init_db):
    user = init_db.query(User).filter_by(username="testadmin").first()
    with app.app_context():
        token = create_access_token(
            identity=str(user.id),
            additional_claims={"role": "administrator"},
        )
    return {"Authorization": f"Bearer {token}"}


def test_create_reservation(client, init_db, auth_headers):
    room = init_db.query(Room).first()
    response = client.post(
        "/api/v1/reservations",
        headers=auth_headers,
        json={
            "reservationNumber": "RES12345",
            "startDate": "2025-02-10",
            "endDate": "2025-02-15",
            "roomName": room.name,
            "structureId": room.id_structure,
            "email": "guest@example.com",
        },
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["reservation"]["reservationNumber"] == "RES12345"
    assert data["reservation"]["startDate"] == "2025-02-10"


def test_create_reservation_missing_fields(client, init_db, auth_headers):
    response = client.post(
        "/api/v1/reservations", headers=auth_headers, json={"reservationNumber": "RES12345"}
    )
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_create_reservation_invalid_date(client, init_db, auth_headers):
    room = init_db.query(Room).first()
    response = client.post(
        "/api/v1/reservations",
        headers=auth_headers,
        json={
            "reservationNumber": "RES12346",
            "startDate": "10-02-2025",
            "endDate": "15-02-2025",
            "roomName": room.name,
            "structureId": room.id_structure,
            "email": "guest@example.com",
        },
    )
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_create_reservation_room_not_found(client, init_db, auth_headers):
    response = client.post(
        "/api/v1/reservations",
        headers=auth_headers,
        json={
            "reservationNumber": "RES12347",
            "startDate": "2025-02-10",
            "endDate": "2025-02-15",
            "roomName": "NonExistentRoom",
            "structureId": 1,
            "email": "guest@example.com",
        },
    )
    assert response.status_code == 404
    assert "error" in response.get_json()


def test_get_reservations(client, init_db, auth_headers):
    response = client.get("/api/v1/reservations", headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert "reservations" in data


def test_get_reservation_per_month(client, init_db, auth_headers):
    structure = init_db.query(Structure).first()
    room = init_db.query(Room).first()
    reservations = [
       Reservation(id_reference="RES1001", start_date="2025-01-10", end_date="2025-01-15", id_room=room.id, status="Pending", email="guest1@example.com"),
       Reservation(id_reference="RES1002", start_date="2025-02-05", end_date="2025-02-10", id_room=room.id, status="Pending", email="guest2@example.com"),
    ]
    init_db.add_all(reservations)
    init_db.commit()

    response = client.get(f"/api/v1/reservations/monthly/{structure.id}", headers=auth_headers)
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



def test_get_reservations_per_month_basic(client, init_db, auth_headers):
    """Test normal reservation retrieval per month."""
    db = init_db
    structure_id = db.query(Structure).first().id

    # Add reservations for different months
    room = db.query(Room).first()
    reservation1 = Reservation(
        id_reference="RES1", start_date=datetime(2024, 1, 10), end_date=datetime(2024, 1, 15), id_room=room.id, email="guest1@example.com"
    )
    reservation2 = Reservation(
        id_reference="RES2", start_date=datetime(2024, 2, 5), end_date=datetime(2024, 2, 10), id_room=room.id, email="guest2@example.com"
    )

    db.add_all([reservation1, reservation2])
    db.commit()

    response = client.get(f"/api/v1/reservations/monthly/{structure_id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 12  # 12 months
    assert any(item['month'] == 'January' and item['total_reservations'] == 1 for item in data)
    assert any(item['month'] == 'February' and item['total_reservations'] == 1 for item in data)


def test_get_reservations_per_month_no_reservations(client, init_db, auth_headers):
    """Test the scenario where there are no reservations for the structure."""
    db = init_db
    structure_id = db.query(Structure).first().id

    response = client.get(f"/api/v1/reservations/monthly/{structure_id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 12  # 12 months
    assert all(item['total_reservations'] == 0 for item in data)


def test_get_reservations_per_month_invalid_structure_id(client, init_db, auth_headers):
    """Test the scenario where an invalid structure_id is provided."""
    invalid_structure_id = 9999  # Assuming this structure ID doesn't exist

    response = client.get(f"/api/v1/reservations/monthly/{invalid_structure_id}", headers=auth_headers)

    assert response.status_code == 403
    data = response.get_json()
    assert data["error"] == "Access denied for this structure"

    """Test when no reservations exist for a structure."""
    """ _, structure_id = init_db  # DB is clean from fixture """

    response = client.get("/api/v1/reservations/monthly/1", headers=auth_headers)
    assert response.status_code == 200

    data = response.get_json()
    assert len(data) == 12  # 12 months
    assert all(month["total_reservations"] == 0 for month in data)  # No reservations, so all months should be 0


def test_create_reservation_end_before_start_returns_400(client, init_db, auth_headers):
    """Validation: endDate before startDate must be rejected with standard error envelope."""
    room = init_db.query(Room).first()
    response = client.post(
        "/api/v1/reservations",
        headers=auth_headers,
        json={
            "reservationNumber": "RES-END-BEFORE-START",
            "startDate": "2025-03-15",
            "endDate": "2025-03-10",
            "roomName": room.name,
            "structureId": room.id_structure,
            "email": "guest@example.com",
        },
    )
    assert response.status_code == 400
    payload = response.get_json()
    assert "error" in payload
    assert "Traceback" not in payload["error"]


def test_create_reservation_invalid_room_id_type_returns_400(client, init_db, auth_headers):
    """Validation: roomId must be an integer."""
    response = client.post(
        "/api/v1/reservations",
        headers=auth_headers,
        json={
            "reservationNumber": "RES-BAD-ROOMID",
            "startDate": "2025-03-10",
            "endDate": "2025-03-15",
            "roomId": "bad-id",
            "email": "guest@example.com",
        },
    )
    assert response.status_code == 400
    payload = response.get_json()
    assert payload["error"] == "Invalid roomId. Must be an integer."


def test_create_reservation_people_over_capacity_returns_400(client, init_db, auth_headers):
    """Validation: numberOfPeople cannot exceed room capacity."""
    room = init_db.query(Room).first()
    response = client.post(
        "/api/v1/reservations",
        headers=auth_headers,
        json={
            "reservationNumber": "RES-OVER-CAP",
            "startDate": "2025-04-10",
            "endDate": "2025-04-12",
            "roomId": room.id,
            "numberOfPeople": room.capacity + 1,
            "email": "guest@example.com",
        },
    )
    assert response.status_code == 400
    payload = response.get_json()
    assert "error" in payload
    assert "cannot exceed room capacity" in payload["error"]
    assert "sqlalchemy" not in payload["error"].lower()


def test_create_reservation_invalid_structure_id_type_returns_400(client, init_db, auth_headers):
    """Validation: structureId must be an integer when roomName is used."""
    room = init_db.query(Room).first()
    response = client.post(
        "/api/v1/reservations",
        headers=auth_headers,
        json={
            "reservationNumber": "RES-BAD-STRUCTURE",
            "startDate": "2025-05-01",
            "endDate": "2025-05-03",
            "roomName": room.name,
            "structureId": "not-an-int",
            "email": "guest@example.com",
        },
    )
    assert response.status_code == 400
    payload = response.get_json()
    assert payload["error"] == "Invalid structureId. Must be an integer."


def test_update_reservation_success(client, init_db, auth_headers):
    """PATCH updates allowed fields and returns updated reservation payload."""
    room = init_db.query(Room).first()
    reservation = Reservation(
        id_reference="RES-UPD-01",
        start_date="2025-06-01",
        end_date="2025-06-03",
        id_room=room.id,
        email="guest-update@example.com",
        number_of_people=1,
    )
    init_db.add(reservation)
    init_db.commit()
    init_db.refresh(reservation)

    response = client.patch(
        f"/api/v1/reservations/{reservation.id}",
        headers=auth_headers,
        json={
            "status": "Approved",
            "number_of_people": 2,
        },
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["reservation"]["status"] == "Approved"
    assert payload["reservation"]["numberOfPeople"] == 2


def test_update_reservation_invalid_number_type_returns_400(client, init_db, auth_headers):
    """PATCH rejects non-numeric number_of_people."""
    room = init_db.query(Room).first()
    reservation = Reservation(
        id_reference="RES-UPD-02",
        start_date="2025-06-01",
        end_date="2025-06-03",
        id_room=room.id,
        email="guest-update2@example.com",
    )
    init_db.add(reservation)
    init_db.commit()
    init_db.refresh(reservation)

    response = client.patch(
        f"/api/v1/reservations/{reservation.id}",
        headers=auth_headers,
        json={"number_of_people": "not-a-number"},
    )
    assert response.status_code == 400
    payload = response.get_json()
    assert "error" in payload
    assert "Invalid number of people" in payload["error"]
    assert "Traceback" not in payload["error"]


def test_update_reservation_people_over_capacity_returns_400(client, init_db, auth_headers):
    """PATCH enforces room capacity boundary."""
    room = init_db.query(Room).first()
    reservation = Reservation(
        id_reference="RES-UPD-03",
        start_date="2025-06-01",
        end_date="2025-06-03",
        id_room=room.id,
        email="guest-update3@example.com",
        number_of_people=1,
    )
    init_db.add(reservation)
    init_db.commit()
    init_db.refresh(reservation)

    response = client.patch(
        f"/api/v1/reservations/{reservation.id}",
        headers=auth_headers,
        json={"number_of_people": room.capacity + 1},
    )
    assert response.status_code == 400
    payload = response.get_json()
    assert "cannot exceed room capacity" in payload["error"]


def test_update_reservation_target_room_not_found_returns_404(client, init_db, auth_headers):
    """PATCH returns 404 when target room id does not exist."""
    room = init_db.query(Room).first()
    reservation = Reservation(
        id_reference="RES-UPD-04",
        start_date="2025-06-01",
        end_date="2025-06-03",
        id_room=room.id,
        email="guest-update4@example.com",
    )
    init_db.add(reservation)
    init_db.commit()
    init_db.refresh(reservation)

    response = client.patch(
        f"/api/v1/reservations/{reservation.id}",
        headers=auth_headers,
        json={"room": {"id": 999999}},
    )
    assert response.status_code == 404
    assert response.get_json()["error"] == "Target room not found"


def test_delete_reservation_success(client, init_db, auth_headers):
    """DELETE removes reservation and returns success message."""
    room = init_db.query(Room).first()
    reservation = Reservation(
        id_reference="RES-DEL-01",
        start_date="2025-06-01",
        end_date="2025-06-03",
        id_room=room.id,
        email="guest-delete@example.com",
    )
    init_db.add(reservation)
    init_db.commit()
    init_db.refresh(reservation)

    response = client.delete(
        f"/api/v1/reservations/{reservation.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert "deleted successfully" in response.get_json()["message"]

    deleted = init_db.query(Reservation).filter(Reservation.id == reservation.id).first()
    assert deleted is None


def test_delete_reservation_not_found_returns_404(client, init_db, auth_headers):
    """DELETE returns 404 for unknown reservation id."""
    response = client.delete("/api/v1/reservations/999999", headers=auth_headers)
    assert response.status_code == 404
    payload = response.get_json()
    assert "error" in payload
    assert "not found" in payload["error"].lower()
