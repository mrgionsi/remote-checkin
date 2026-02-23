"""Contract tests for GET /api/v1/reservations/check/<reservation_id>."""

# pylint: disable=redefined-outer-name,C0411

from datetime import date

from flask import Flask
from itsdangerous import URLSafeTimedSerializer
import pytest
from sqlalchemy.exc import SQLAlchemyError

from database import Base, SessionLocal, engine
from models import Client, ClientReservations, Reservation, Room, Structure
from routes import reservation_routes
from routes.reservation_routes import UPLOAD_TOKEN_SALT, reservation_bp


class _FailingSession:
    """Session stub that raises SQLAlchemyError on query usage."""

    def query(self, *_args, **_kwargs):
        """Simulate a query that always raises a SQLAlchemyError."""
        raise SQLAlchemyError("db down")

    def close(self):
        """No-op close."""


@pytest.fixture(scope="module")
def app():
    """Create Flask app exposing reservation routes."""
    flask_app = Flask(__name__)
    flask_app.config.from_object("config.TestConfig")
    flask_app.config["JWT_SECRET_KEY"] = "test-secret"
    flask_app.register_blueprint(reservation_bp)
    Base.metadata.create_all(bind=engine)
    yield flask_app
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(app):
    """Return Flask test client."""
    return app.test_client()


@pytest.fixture()
def seed_reservations():
    """Seed reservations used by reservation-check contract tests."""
    db = SessionLocal()
    db.query(ClientReservations).delete()
    db.query(Client).delete()
    db.query(Reservation).delete()
    db.query(Room).delete()
    db.query(Structure).delete()
    db.commit()

    structure = Structure(name="Contract Structure", city="Rome", street="A Street")
    db.add(structure)
    db.commit()
    db.refresh(structure)

    room = Room(name="Contract Room", capacity=3, id_structure=structure.id)
    db.add(room)
    db.commit()
    db.refresh(room)

    reservation_default = Reservation(
        id_reference="CHK-CONTRACT-001",
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 5),
        id_room=room.id,
        email="guest@example.com",
        number_of_people=2,
    )
    reservation_zero = Reservation(
        id_reference="CHK-CONTRACT-ZERO",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 4, 4),
        id_room=room.id,
        email="guest2@example.com",
        number_of_people=0,
    )
    db.add_all([reservation_default, reservation_zero])
    db.commit()
    db.refresh(reservation_default)

    guest = Client(name="John", surname="Doe")
    db.add(guest)
    db.commit()
    db.refresh(guest)
    db.add(ClientReservations(id_reservation=reservation_default.id, id_client=guest.id))
    db.commit()
    db.close()

    return {
        "default_ref": "CHK-CONTRACT-001",
        "zero_ref": "CHK-CONTRACT-ZERO",
    }


def test_check_contract_success_payload_and_token(client, app, seed_reservations):
    """Successful check response includes expected keys, values and signed token."""
    response = client.get(f"/api/v1/reservations/check/{seed_reservations['default_ref']}")
    assert response.status_code == 200
    payload = response.get_json()

    for required_key in ("id", "id_reference", "number_of_people", "registered_clients_count", "status", "upload_token"):
        assert required_key in payload

    assert payload["id_reference"] == seed_reservations["default_ref"]
    assert payload["number_of_people"] == 2
    assert payload["registered_clients_count"] == 1
    assert isinstance(payload["registered_clients_count"], int)

    serializer = URLSafeTimedSerializer(app.config["JWT_SECRET_KEY"])
    decoded = serializer.loads(payload["upload_token"], salt=UPLOAD_TOKEN_SALT, max_age=120)
    assert decoded["reservation_ref"] == seed_reservations["default_ref"]


def test_check_contract_number_of_people_zero_falls_back_to_one(client, seed_reservations):
    """number_of_people uses safe fallback to 1 when persisted value is zero."""
    response = client.get(f"/api/v1/reservations/check/{seed_reservations['zero_ref']}")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["number_of_people"] == 1
    assert payload["registered_clients_count"] == 0


def test_check_contract_nonexistent_reference_returns_404(client):
    """Unknown reservation reference returns 404 error contract."""
    response = client.get("/api/v1/reservations/check/DOES-NOT-EXIST")
    assert response.status_code == 404
    assert response.get_json()["error"] == "Reservation with ID DOES-NOT-EXIST not found"


def test_check_contract_malformed_reference_returns_404(client):
    """Malformed reservation references are handled safely and return 404."""
    response = client.get("/api/v1/reservations/check/invalid-id")
    assert response.status_code == 404
    assert "error" in response.get_json()


def test_check_contract_db_fault_returns_generic_500(client, monkeypatch):
    """Database failures should return generic 500 payload without internals."""
    monkeypatch.setattr(reservation_routes, "SessionLocal", _FailingSession)
    response = client.get("/api/v1/reservations/check/CHK-CONTRACT-001")
    assert response.status_code == 500
    assert response.get_json()["error"] == "Database error"
