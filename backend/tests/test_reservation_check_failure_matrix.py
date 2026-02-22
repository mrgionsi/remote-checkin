"""Failure-matrix tests for GET /api/v1/reservations/check/<reservation_id>."""

# pylint: disable=redefined-outer-name,wrong-import-order

from datetime import date

from flask import Flask
import pytest
from sqlalchemy.exc import SQLAlchemyError
from itsdangerous import URLSafeTimedSerializer

from database import Base, SessionLocal, engine
from models import Client, ClientReservations, Reservation, Room, Structure
from routes import reservation_routes
from routes.reservation_routes import UPLOAD_TOKEN_SALT, reservation_bp


class _FailingSession:
    """Session stub that raises SQLAlchemyError when queried."""

    def query(self, *_args, **_kwargs):
        """Raise SQLAlchemyError for any query access."""
        raise SQLAlchemyError("db down")

    def close(self):
        """No-op close."""


@pytest.fixture(scope="module")
def app():
    """Build a Flask app with reservation routes for check-endpoint tests."""
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
def seeded_reservation():
    """Create one reservation and one linked client for deterministic checks."""
    db = SessionLocal()
    db.query(ClientReservations).delete()
    db.query(Client).delete()
    db.query(Reservation).delete()
    db.query(Room).delete()
    db.query(Structure).delete()
    db.commit()

    structure = Structure(name="Matrix Structure", street="Street 1", city="Rome")
    db.add(structure)
    db.commit()
    db.refresh(structure)

    room = Room(name="Matrix Room", capacity=2, id_structure=structure.id)
    db.add(room)
    db.commit()
    db.refresh(room)

    reservation = Reservation(
        id_reference="CHK-MATRIX-001",
        start_date=date(2026, 2, 1),
        end_date=date(2026, 2, 5),
        id_room=room.id,
        email="guest@example.com",
        status="Pending",
        number_of_people=2,
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)

    client = Client(name="John", surname="Doe")
    db.add(client)
    db.commit()
    db.refresh(client)

    db.add(ClientReservations(id_reservation=reservation.id, id_client=client.id))
    db.commit()
    reservation_reference = reservation.id_reference
    db.close()

    return reservation_reference


def test_check_reservation_returns_upload_token_and_capacity(client, app, seeded_reservation):
    """Valid reservation reference returns capacity fields and signed upload token."""
    response = client.get(f"/api/v1/reservations/check/{seeded_reservation}")
    assert response.status_code == 200
    payload = response.get_json()

    assert payload["id_reference"] == seeded_reservation
    assert payload["number_of_people"] == 2
    assert payload["registered_clients_count"] == 1
    assert payload["upload_token"]

    serializer = URLSafeTimedSerializer(app.config["JWT_SECRET_KEY"])
    token_payload = serializer.loads(payload["upload_token"], salt=UPLOAD_TOKEN_SALT, max_age=60)
    assert token_payload["reservation_ref"] == seeded_reservation


def test_check_reservation_nonexistent_returns_404(client):
    """Unknown reservation reference returns 404 contract."""
    response = client.get("/api/v1/reservations/check/DOES-NOT-EXIST")
    assert response.status_code == 404
    assert response.get_json()["error"] == "Reservation with ID DOES-NOT-EXIST not found"


def test_check_reservation_malformed_reference_returns_404(client):
    """Malformed reservation references are treated as not found (no crash)."""
    malformed_reference = "invalid-id-format"
    response = client.get(f"/api/v1/reservations/check/{malformed_reference}")
    assert response.status_code == 404
    assert "not found" in response.get_json()["error"].lower()


def test_check_reservation_db_fault_returns_safe_500(client, monkeypatch):
    """DB faults should return generic 500 contract without leaking internals."""
    monkeypatch.setattr(reservation_routes, "SessionLocal", _FailingSession)
    response = client.get("/api/v1/reservations/check/CHK-MATRIX-001")
    assert response.status_code == 500
    payload = response.get_json()
    assert payload["error"] == "Database error"
    assert "db down" not in payload["error"].lower()
