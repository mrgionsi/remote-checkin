"""Status transition and validation tests for reservation status endpoint."""

# pylint: disable=redefined-outer-name

from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
import pytest
from sqlalchemy import text

from models import AdminStructure, Reservation, Role, Room, Structure, User
from routes.reservation_routes import reservation_bp, STATUS_SENT_BACK_TO_CUSTOMER
from database import Base, SessionLocal, engine


@pytest.fixture(scope="module")
def app():
    """Create Flask app for reservation status endpoint tests."""
    flask_app = Flask(__name__)
    flask_app.config.from_object("config.TestConfig")
    flask_app.config["JWT_SECRET_KEY"] = "test-secret"
    flask_app.config["JWT_TOKEN_LOCATION"] = ["headers"]
    JWTManager(flask_app)
    flask_app.register_blueprint(reservation_bp)
    Base.metadata.create_all(bind=engine)
    yield flask_app
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS structure_reservations CASCADE"))
        conn.commit()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(app):
    """Return Flask test client."""
    return app.test_client()


@pytest.fixture()
def seeded():
    """Seed one mapped admin user and one reservation."""
    db = SessionLocal()
    db.query(AdminStructure).delete()
    db.query(Reservation).delete()
    db.query(Room).delete()
    db.query(Structure).delete()
    db.query(User).delete()
    db.query(Role).delete()
    db.commit()

    role = Role(name="administrator")
    db.add(role)
    db.commit()
    db.refresh(role)

    user = User(username="status-admin", password="hashed", id_role=role.id, email="status@example.com")
    db.add(user)
    db.commit()
    db.refresh(user)

    structure = Structure(name="Status Struct", city="Rome", street="Status St")
    db.add(structure)
    db.commit()
    db.refresh(structure)

    db.add(AdminStructure(id_user=user.id, id_structure=structure.id))
    db.commit()

    room = Room(name="Status Room", capacity=2, id_structure=structure.id)
    db.add(room)
    db.commit()
    db.refresh(room)

    reservation = Reservation(
        id_reference="RES-STATUS-1",
        start_date="2026-02-01",
        end_date="2026-02-03",
        status="Pending",
        id_room=room.id,
        email="guest-status@example.com",
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)

    yield {"user_id": user.id, "reservation_id": reservation.id}
    db.close()


def _headers(app, user_id: int) -> dict:
    """Build JWT headers for mapped administrator."""
    with app.app_context():
        token = create_access_token(identity=str(user_id), additional_claims={"role": "administrator"})
    return {"Authorization": f"Bearer {token}"}


def test_status_update_rejects_missing_body(client, app, seeded):
    """PUT status endpoint should reject missing/invalid body."""
    response = client.put(
        f"/api/v1/reservations/{seeded['reservation_id']}/status",
        headers=_headers(app, seeded["user_id"]),
    )
    assert response.status_code == 415


def test_status_update_rejects_missing_status_field(client, app, seeded):
    """PUT status endpoint requires status field."""
    response = client.put(
        f"/api/v1/reservations/{seeded['reservation_id']}/status",
        headers=_headers(app, seeded["user_id"]),
        json={"note": "nothing"},
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "Missing 'status' field"


def test_status_update_rejects_invalid_status_value(client, app, seeded):
    """PUT status endpoint rejects unsupported status values."""
    response = client.put(
        f"/api/v1/reservations/{seeded['reservation_id']}/status",
        headers=_headers(app, seeded["user_id"]),
        json={"status": "SomeUnknownStatus"},
    )
    assert response.status_code == 400
    assert "Invalid status." in response.get_json()["error"]


def test_status_update_allows_valid_values(client, app, seeded):
    """PUT status endpoint accepts each supported value."""
    for status in ["Pending", "Declined", "Approved", STATUS_SENT_BACK_TO_CUSTOMER]:
        response = client.put(
            f"/api/v1/reservations/{seeded['reservation_id']}/status",
            headers=_headers(app, seeded["user_id"]),
            json={"status": status},
        )
        assert response.status_code == 200
        assert response.get_json()["reservation"]["status"] == status


def test_status_update_not_found_returns_404(client, app, seeded):
    """PUT status endpoint returns 404 for unknown reservation."""
    response = client.put(
        "/api/v1/reservations/999999/status",
        headers=_headers(app, seeded["user_id"]),
        json={"status": "Pending"},
    )
    assert response.status_code == 404
    assert "not found" in response.get_json()["error"].lower()
