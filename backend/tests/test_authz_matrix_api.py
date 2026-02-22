"""AuthZ matrix tests for tenant-boundary sensitive API routes."""

# pylint: disable=all

from pathlib import Path
import shutil

import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from sqlalchemy import text

from database import Base, SessionLocal, engine
from models import (
    AdminStructure,
    Client,
    ClientReservations,
    Reservation,
    Role,
    Room,
    Structure,
    User,
)
from routes.client_reservation_routes import client_reservation_bp
from routes.reservation_routes import reservation_bp
from routes.room_routes import room_bp


UPLOADS_DIR = Path("uploads")


@pytest.fixture(scope="module")
def app():
    """Create a Flask app with JWT and the tested blueprints."""
    flask_app = Flask(__name__)
    flask_app.config.from_object("config.TestConfig")
    flask_app.config["JWT_SECRET_KEY"] = "test-secret"
    JWTManager(flask_app)
    flask_app.register_blueprint(room_bp)
    flask_app.register_blueprint(reservation_bp)
    flask_app.register_blueprint(client_reservation_bp)
    Base.metadata.create_all(bind=engine)
    yield flask_app
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS structure_reservations CASCADE"))
        conn.commit()
    Base.metadata.drop_all(bind=engine)
    if UPLOADS_DIR.exists():
        shutil.rmtree(UPLOADS_DIR, ignore_errors=True)


@pytest.fixture
def client(app):
    """Return Flask test client."""
    return app.test_client()


@pytest.fixture
def seed_data():
    """Create users, structures, mappings, rooms, reservations and one client link."""
    db = SessionLocal()
    db.query(AdminStructure).delete()
    db.query(ClientReservations).delete()
    db.query(Client).delete()
    db.query(Reservation).delete()
    db.query(Room).delete()
    db.query(Structure).delete()
    db.query(User).delete()
    db.query(Role).delete()
    db.commit()

    admin_role = Role(name="administrator")
    super_role = Role(name="superadmin")
    db.add_all([admin_role, super_role])
    db.commit()
    db.refresh(admin_role)
    db.refresh(super_role)

    mapped_admin = User(
        username="mapped-admin",
        password="hashed",
        id_role=admin_role.id,
        email="mapped@example.com",
    )
    unmapped_admin = User(
        username="unmapped-admin",
        password="hashed",
        id_role=admin_role.id,
        email="unmapped@example.com",
    )
    superadmin = User(
        username="super-admin",
        password="hashed",
        id_role=super_role.id,
        email="super@example.com",
    )
    db.add_all([mapped_admin, unmapped_admin, superadmin])
    db.commit()
    db.refresh(mapped_admin)
    db.refresh(unmapped_admin)
    db.refresh(superadmin)

    structure_a = Structure(name="Structure A", city="Rome", street="A St")
    structure_b = Structure(name="Structure B", city="Milan", street="B St")
    db.add_all([structure_a, structure_b])
    db.commit()
    db.refresh(structure_a)
    db.refresh(structure_b)

    db.add(AdminStructure(id_user=mapped_admin.id, id_structure=structure_a.id))
    db.commit()

    room_a = Room(name="Room A", capacity=2, id_structure=structure_a.id)
    room_b = Room(name="Room B", capacity=3, id_structure=structure_b.id)
    db.add_all([room_a, room_b])
    db.commit()
    db.refresh(room_a)
    db.refresh(room_b)

    reservation_a = Reservation(
        id_reference="RES-A",
        start_date="2026-01-10",
        end_date="2026-01-12",
        id_room=room_a.id,
        email="guesta@example.com",
    )
    reservation_b = Reservation(
        id_reference="RES-B",
        start_date="2026-01-14",
        end_date="2026-01-16",
        id_room=room_b.id,
        email="guestb@example.com",
    )
    db.add_all([reservation_a, reservation_b])
    db.commit()
    db.refresh(reservation_a)
    db.refresh(reservation_b)

    guest = Client(name="John", surname="Doe", cf="DOEJHN90A01H501X")
    db.add(guest)
    db.commit()
    db.refresh(guest)
    db.add(ClientReservations(id_client=guest.id, id_reservation=reservation_a.id))
    db.commit()

    reservation_upload_dir = UPLOADS_DIR / reservation_a.id_reference
    reservation_upload_dir.mkdir(parents=True, exist_ok=True)
    (reservation_upload_dir / "doc.jpg").write_bytes(b"fake-jpg")

    yield {
        "mapped_admin_id": mapped_admin.id,
        "unmapped_admin_id": unmapped_admin.id,
        "superadmin_id": superadmin.id,
        "structure_a_id": structure_a.id,
        "structure_b_id": structure_b.id,
        "room_a_id": room_a.id,
        "room_b_id": room_b.id,
        "reservation_a_id": reservation_a.id,
        "reservation_b_id": reservation_b.id,
        "reservation_a_ref": reservation_a.id_reference,
    }
    db.close()


def _auth_header(app, user_id: int, role: str) -> dict:
    """Build auth header for a given test user and role."""
    with app.app_context():
        token = create_access_token(identity=str(user_id), additional_claims={"role": role})
    return {"Authorization": f"Bearer {token}"}


def test_rooms_structure_scope(client, app, seed_data):
    """Mapped admin can access own structure but not others."""
    mapped = _auth_header(app, seed_data["mapped_admin_id"], "administrator")
    resp_allowed = client.get(f"/api/v1/rooms?structure_id={seed_data['structure_a_id']}", headers=mapped)
    resp_denied = client.get(f"/api/v1/rooms?structure_id={seed_data['structure_b_id']}", headers=mapped)
    assert resp_allowed.status_code == 200
    assert resp_denied.status_code == 403


def test_room_detail_and_write_scope(client, app, seed_data):
    """Room detail/update/delete enforce structure boundaries for mapped admin."""
    mapped = _auth_header(app, seed_data["mapped_admin_id"], "administrator")

    own_room = client.get(f"/api/v1/rooms/{seed_data['room_a_id']}", headers=mapped)
    foreign_room = client.get(f"/api/v1/rooms/{seed_data['room_b_id']}", headers=mapped)
    assert own_room.status_code == 200
    assert foreign_room.status_code == 403

    forbidden_update = client.put(
        f"/api/v1/rooms/{seed_data['room_b_id']}",
        headers=mapped,
        json={"name": "Should Not Update", "capacity": 3, "id_structure": seed_data["structure_b_id"]},
    )
    forbidden_delete = client.delete(f"/api/v1/rooms/{seed_data['room_b_id']}", headers=mapped)
    assert forbidden_update.status_code == 403
    assert forbidden_delete.status_code == 403


def test_rooms_unmapped_admin_gets_empty_list(client, app, seed_data):
    """Unmapped admin gets empty list on generic rooms query."""
    unmapped = _auth_header(app, seed_data["unmapped_admin_id"], "administrator")
    response = client.get("/api/v1/rooms", headers=unmapped)
    assert response.status_code == 200
    assert response.get_json() == []


def test_rooms_superadmin_can_read_all(client, app, seed_data):
    """Superadmin can list all rooms without structure filter."""
    superadmin = _auth_header(app, seed_data["superadmin_id"], "superadmin")
    response = client.get("/api/v1/rooms", headers=superadmin)
    assert response.status_code == 200
    room_names = {room["name"] for room in response.get_json()}
    assert {"Room A", "Room B"}.issubset(room_names)


def test_reservation_monthly_scope(client, app, seed_data):
    """Monthly reservation endpoint enforces structure boundary."""
    mapped = _auth_header(app, seed_data["mapped_admin_id"], "administrator")
    ok = client.get(f"/api/v1/reservations/monthly/{seed_data['structure_a_id']}", headers=mapped)
    forbidden = client.get(f"/api/v1/reservations/monthly/{seed_data['structure_b_id']}", headers=mapped)
    assert ok.status_code == 200
    assert forbidden.status_code == 403


def test_reservation_structure_scope(client, app, seed_data):
    """Structure reservations endpoint enforces structure boundary."""
    mapped = _auth_header(app, seed_data["mapped_admin_id"], "administrator")
    ok = client.get(f"/api/v1/reservations/structure/{seed_data['structure_a_id']}", headers=mapped)
    forbidden = client.get(f"/api/v1/reservations/structure/{seed_data['structure_b_id']}", headers=mapped)
    assert ok.status_code == 200
    assert forbidden.status_code == 403


def test_reservation_admin_detail_scope(client, app, seed_data):
    """Admin reservation-detail endpoint enforces structure boundaries."""
    mapped = _auth_header(app, seed_data["mapped_admin_id"], "administrator")
    allowed = client.get(f"/api/v1/reservations/admin/{seed_data['reservation_a_id']}", headers=mapped)
    forbidden = client.get(f"/api/v1/reservations/admin/{seed_data['reservation_b_id']}", headers=mapped)
    assert allowed.status_code == 200
    assert forbidden.status_code == 403


def test_reservation_write_scope(client, app, seed_data):
    """Reservation update/delete and create enforce structure boundaries."""
    mapped = _auth_header(app, seed_data["mapped_admin_id"], "administrator")

    forbidden_patch = client.patch(
        f"/api/v1/reservations/{seed_data['reservation_b_id']}",
        headers=mapped,
        json={"status": "Approved"},
    )
    forbidden_delete = client.delete(
        f"/api/v1/reservations/{seed_data['reservation_b_id']}",
        headers=mapped,
    )
    assert forbidden_patch.status_code == 403
    assert forbidden_delete.status_code == 403

    forbidden_create = client.post(
        "/api/v1/reservations",
        headers=mapped,
        json={
            "reservationNumber": "RES-CROSS-SCOPE",
            "startDate": "2026-02-20",
            "endDate": "2026-02-23",
            "roomId": seed_data["room_b_id"],
            "structureId": seed_data["structure_b_id"],
            "email": "cross@example.com",
        },
    )
    assert forbidden_create.status_code == 403

def test_clients_endpoint_scope(client, app, seed_data):
    """Clients-by-reservation endpoint only allows authorized users."""
    mapped = _auth_header(app, seed_data["mapped_admin_id"], "administrator")
    unmapped = _auth_header(app, seed_data["unmapped_admin_id"], "administrator")
    ok = client.get(f"/api/v1/reservations/{seed_data['reservation_a_id']}/clients", headers=mapped)
    forbidden = client.get(f"/api/v1/reservations/{seed_data['reservation_a_id']}/clients", headers=unmapped)
    assert ok.status_code == 200
    assert forbidden.status_code == 403


def test_images_endpoint_scope(client, app, seed_data):
    """Image retrieval respects reservation structure boundaries."""
    mapped = _auth_header(app, seed_data["mapped_admin_id"], "administrator")
    unmapped = _auth_header(app, seed_data["unmapped_admin_id"], "administrator")
    image_path = f"/api/v1/images/{seed_data['reservation_a_ref']}/doc.jpg"
    ok = client.get(image_path, headers=mapped)
    forbidden = client.get(image_path, headers=unmapped)
    assert ok.status_code == 200
    assert forbidden.status_code == 403
