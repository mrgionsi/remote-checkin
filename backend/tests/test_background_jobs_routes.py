"""Tests for background-job queue endpoints in admin routes."""

# pylint: disable=redefined-outer-name,import-error,C0411

import json
from uuid import uuid4

import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from sqlalchemy.orm import close_all_sessions

from models import (
    AdminStructure,
    BackgroundJob,
    Client,
    ClientReservations,
    Reservation,
    Role,
    Room,
    Structure,
    User,
)
from routes.admin_routes import admin_bp
from database import Base, SessionLocal, engine


@pytest.fixture(scope="module")
def app():
    """Build app with admin routes for queue endpoint testing."""
    flask_app = Flask(__name__)
    flask_app.config.from_object("config.TestConfig")
    flask_app.config["JWT_SECRET_KEY"] = "test-secret"
    flask_app.config["JWT_TOKEN_LOCATION"] = ["headers"]
    JWTManager(flask_app)
    flask_app.register_blueprint(admin_bp)
    Base.metadata.create_all(bind=engine)
    yield flask_app
    close_all_sessions()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def client(app):
    """Return Flask test client."""
    return app.test_client()


def _auth_headers(app, identity: str, role: str = "administrator") -> dict:
    with app.app_context():
        token = create_access_token(identity=identity, additional_claims={"role": role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def seeded_entities():
    """Seed minimum reservation/client/structure data for queue tests."""
    db = SessionLocal()
    suffix = uuid4().hex[:8]
    base_id = int(uuid4().int % 1_000_000_000)

    role = db.query(Role).filter(Role.name == "administrator").first()
    if role is None:
        role = Role(name="administrator")
        db.add(role)
        db.commit()
        db.refresh(role)

    user = User(
        id=base_id + 1,
        username=f"queue-admin-{suffix}",
        password="hashed",
        email=f"queue-admin-{suffix}@example.com",
        id_role=role.id,
        portale_username="demo-user",
        portale_password="encrypted-pw",
        portale_wskey="demo-ws-key",
    )
    db.add(user)

    structure = Structure(id=base_id + 2, name=f"Queue Structure {suffix}", city="Rome")
    db.add(structure)
    db.flush()

    association = AdminStructure(id_user=user.id, id_structure=structure.id)
    db.add(association)

    room = Room(id=base_id + 3, name=f"Queue Room {suffix}", capacity=2, id_structure=structure.id)
    db.add(room)
    db.flush()

    reservation = Reservation(
        id=base_id + 4,
        id_reference=f"RES-{suffix}",
        start_date=None,
        end_date=None,
        id_room=room.id,
        status="Approved",
        name_reference="Queue Reservation",
        email=f"guest-{suffix}@example.com",
    )
    db.add(reservation)
    db.flush()

    guest = Client(id=base_id + 5, name="Guest", surname="Queue")
    db.add(guest)
    db.flush()

    db.add(ClientReservations(id_reservation=reservation.id, id_client=guest.id))
    db.commit()

    payload = {
        "user_id": user.id,
        "structure_id": structure.id,
        "room_id": room.id,
        "reservation_id": reservation.id,
    }

    yield payload

    db.query(ClientReservations).filter(ClientReservations.id_reservation == reservation.id).delete()
    db.query(Client).filter(Client.id == guest.id).delete()
    db.query(Reservation).filter(Reservation.id == reservation.id).delete()
    db.query(Room).filter(Room.id == room.id).delete()
    db.query(AdminStructure).filter(
        AdminStructure.id_user == user.id,
        AdminStructure.id_structure == structure.id,
    ).delete()
    db.query(Structure).filter(Structure.id == structure.id).delete()
    db.query(User).filter(User.id == user.id).delete()
    db.commit()
    db.close()


def test_queue_portale_submission_creates_job(client, app, seeded_entities):
    """Queue endpoint creates a queued background job and returns 202."""
    headers = _auth_headers(app, identity=str(seeded_entities["user_id"]))

    response = client.post(
        f"/api/v1/admin/reservations/{seeded_entities['reservation_id']}/queue-portale-alloggi-real",
        headers=headers,
    )

    assert response.status_code == 202
    payload = response.get_json()
    assert payload["job"]["job_type"] == "portale_alloggi_submit"
    assert payload["job"]["status"] == "queued"

    db = SessionLocal()
    job = db.query(BackgroundJob).filter(BackgroundJob.id == payload["job"]["id"]).first()
    assert job is not None
    assert job.structure_id == seeded_entities["structure_id"]
    assert json.loads(job.payload_json)["reservation_id"] == seeded_entities["reservation_id"]
    db.query(BackgroundJob).filter(BackgroundJob.id == job.id).delete()
    db.commit()
    db.close()


def test_queue_portale_submission_rejects_non_approved_status(client, app, seeded_entities):
    """Queue endpoint rejects reservation when status is not Approved."""
    db = SessionLocal()
    reservation = db.query(Reservation).filter(Reservation.id == seeded_entities["reservation_id"]).first()
    reservation.status = "Pending"
    db.commit()
    db.close()

    headers = _auth_headers(app, identity=str(seeded_entities["user_id"]))
    response = client.post(
        f"/api/v1/admin/reservations/{seeded_entities['reservation_id']}/queue-portale-alloggi-real",
        headers=headers,
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Reservation not approved"

    db = SessionLocal()
    reservation = db.query(Reservation).filter(Reservation.id == seeded_entities["reservation_id"]).first()
    reservation.status = "Approved"
    db.commit()
    db.close()


def test_recent_jobs_scope_filters_by_admin_visibility(client, app, seeded_entities):
    """Recent jobs endpoint returns only jobs visible to current admin."""
    db = SessionLocal()

    invisible_structure = Structure(
        id=int(uuid4().int % 1_000_000_000),
        name=f"Hidden {uuid4().hex[:6]}",
        city="Naples",
    )
    db.add(invisible_structure)
    db.flush()

    visible_job = BackgroundJob(
        job_type="portale_alloggi_submit",
        status="queued",
        payload_json=json.dumps({"reservation_id": seeded_entities["reservation_id"]}),
        created_by_user_id=seeded_entities["user_id"],
        structure_id=seeded_entities["structure_id"],
    )
    hidden_job = BackgroundJob(
        job_type="portale_alloggi_submit",
        status="queued",
        payload_json=json.dumps({"reservation_id": 999999}),
        created_by_user_id=999999,
        structure_id=invisible_structure.id,
    )
    db.add_all([visible_job, hidden_job])
    db.commit()

    headers = _auth_headers(app, identity=str(seeded_entities["user_id"]))
    response = client.get("/api/v1/admin/jobs/recent?limit=10", headers=headers)

    assert response.status_code == 200
    items = response.get_json()["items"]
    ids = {item["id"] for item in items}
    assert visible_job.id in ids
    assert hidden_job.id not in ids

    db.query(BackgroundJob).filter(BackgroundJob.id.in_([visible_job.id, hidden_job.id])).delete(
        synchronize_session=False
    )
    db.query(Structure).filter(Structure.id == invisible_structure.id).delete()
    db.commit()
    db.close()
