"""Negative scenario matrix for superadmin management endpoints."""

# pylint: disable=redefined-outer-name

from uuid import uuid4

import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from sqlalchemy import text

from models import AdminStructure, Reservation, Role, Room, Structure, User
from routes.superadmin_routes import superadmin_bp
from database import Base, SessionLocal, engine


@pytest.fixture(scope="module")
def app():
    """Create a Flask app with JWT and superadmin routes."""
    flask_app = Flask(__name__)
    flask_app.config.from_object("config.TestConfig")
    flask_app.config["JWT_SECRET_KEY"] = "test-secret"
    flask_app.config["JWT_TOKEN_LOCATION"] = ["headers"]
    JWTManager(flask_app)
    flask_app.register_blueprint(superadmin_bp)
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
def seed_data():
    """Seed roles, users, structures, room, reservation and one association."""
    db = SessionLocal()
    db.query(AdminStructure).delete()
    db.query(Reservation).delete()
    db.query(Room).delete()
    db.query(Structure).delete()
    db.query(User).delete()
    db.query(Role).delete()
    db.commit()

    role_admin = Role(name="administrator")
    role_super = Role(name="superadmin")
    role_guest = Role(name="guest")
    db.add_all([role_admin, role_super, role_guest])
    db.commit()
    db.refresh(role_admin)
    db.refresh(role_super)
    db.refresh(role_guest)

    suffix = uuid4().hex[:8]
    super_user = User(
        username=f"sup-{suffix}",
        password="hashed",
        id_role=role_super.id,
        email=f"sup-{suffix}@example.com",
    )
    admin_user = User(
        username=f"adm-{suffix}",
        password="hashed",
        id_role=role_admin.id,
        email=f"adm-{suffix}@example.com",
    )
    admin_user_2 = User(
        username=f"adm2-{suffix}",
        password="hashed",
        id_role=role_admin.id,
        email=f"adm2-{suffix}@example.com",
    )
    db.add_all([super_user, admin_user, admin_user_2])
    db.commit()
    db.refresh(super_user)
    db.refresh(admin_user)
    db.refresh(admin_user_2)

    structure_a = Structure(name=f"Struct A {suffix}", city="Rome", street="Via A", is_active=True)
    structure_b = Structure(name=f"Struct B {suffix}", city="Milan", street="Via B", is_active=True)
    db.add_all([structure_a, structure_b])
    db.commit()
    db.refresh(structure_a)
    db.refresh(structure_b)

    db.add(AdminStructure(id_user=admin_user.id, id_structure=structure_a.id))
    db.commit()

    room = Room(name=f"Room {suffix}", capacity=2, id_structure=structure_a.id)
    db.add(room)
    db.commit()
    db.refresh(room)

    reservation = Reservation(
        id_reference=f"RES-{suffix}",
        start_date="2026-01-01",
        end_date="2026-01-03",
        id_room=room.id,
        email=f"guest-{suffix}@example.com",
    )
    db.add(reservation)
    db.commit()

    yield {
        "super_user_id": super_user.id,
        "admin_user_id": admin_user.id,
        "admin_user_2_id": admin_user_2.id,
        "role_admin_id": role_admin.id,
        "role_guest_id": role_guest.id,
        "structure_a_id": structure_a.id,
        "structure_b_id": structure_b.id,
        "admin_user_username": admin_user.username,
        "admin_user_2_username": admin_user_2.username,
    }
    db.close()


def _auth_headers(app, user_id: int, role: str) -> dict:
    """Build JWT auth header with role claim."""
    with app.app_context():
        token = create_access_token(identity=str(user_id), additional_claims={"role": role})
    return {"Authorization": f"Bearer {token}"}


def test_structures_requires_superadmin_role(client, app, seed_data):
    """GET structures rejects non-superadmin users."""
    headers = _auth_headers(app, seed_data["admin_user_id"], "administrator")
    response = client.get("/api/v1/superadmin/structures", headers=headers)
    assert response.status_code == 403
    assert "error" in response.get_json()


def test_create_structure_missing_required_fields(client, app, seed_data):
    """POST structures validates required name/city."""
    headers = _auth_headers(app, seed_data["super_user_id"], "superadmin")
    response = client.post(
        "/api/v1/superadmin/structures",
        headers=headers,
        json={"street": "Only Street"},
    )
    assert response.status_code == 400
    assert response.get_json()["message"] == "Structure name and city are required"


def test_create_structure_duplicate_name_city(client, app, seed_data):
    """POST structures rejects duplicate (name, city)."""
    headers = _auth_headers(app, seed_data["super_user_id"], "superadmin")
    db = SessionLocal()
    existing = db.query(Structure).filter(Structure.id == seed_data["structure_a_id"]).first()
    db.close()
    response = client.post(
        "/api/v1/superadmin/structures",
        headers=headers,
        json={"name": existing.name, "city": existing.city},
    )
    assert response.status_code == 400
    assert response.get_json()["message"] == "A structure with this name and city already exists"


def test_update_structure_not_found(client, app, seed_data):
    """PUT structures returns 404 for unknown structure."""
    headers = _auth_headers(app, seed_data["super_user_id"], "superadmin")
    response = client.put(
        "/api/v1/superadmin/structures/999999",
        headers=headers,
        json={"name": "Nope", "city": "Nowhere"},
    )
    assert response.status_code == 404
    assert response.get_json()["error"] == "Structure not found"


def test_update_structure_empty_required_fields(client, app, seed_data):
    """PUT structures rejects empty name/city after strip."""
    headers = _auth_headers(app, seed_data["super_user_id"], "superadmin")
    response = client.put(
        f"/api/v1/superadmin/structures/{seed_data['structure_a_id']}",
        headers=headers,
        json={"name": "   ", "city": "  "},
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "Name and city are required"


def test_delete_structure_not_found(client, app, seed_data):
    """DELETE structures returns 404 for unknown id."""
    headers = _auth_headers(app, seed_data["super_user_id"], "superadmin")
    response = client.delete("/api/v1/superadmin/structures/999999", headers=headers)
    assert response.status_code == 404
    assert response.get_json()["error"] == "Structure not found"


def test_restore_structure_not_found(client, app, seed_data):
    """POST restore returns 404 for unknown structure id."""
    headers = _auth_headers(app, seed_data["super_user_id"], "superadmin")
    response = client.post("/api/v1/superadmin/structures/999999/restore", headers=headers)
    assert response.status_code == 404
    assert response.get_json()["error"] == "Structure not found"


def test_update_user_not_found(client, app, seed_data):
    """PUT users returns 404 when user does not exist."""
    headers = _auth_headers(app, seed_data["super_user_id"], "superadmin")
    response = client.put(
        "/api/v1/superadmin/users/999999",
        headers=headers,
        json={"name": "Ghost"},
    )
    assert response.status_code == 404
    assert response.get_json()["error"] == "User not found"


def test_update_user_duplicate_username(client, app, seed_data):
    """PUT users rejects username already taken by another user."""
    headers = _auth_headers(app, seed_data["super_user_id"], "superadmin")
    response = client.put(
        f"/api/v1/superadmin/users/{seed_data['admin_user_2_id']}",
        headers=headers,
        json={"username": seed_data["admin_user_username"]},
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "Username already exists"


def test_change_role_invalid_role_id(client, app, seed_data):
    """PUT change-role rejects invalid role id."""
    headers = _auth_headers(app, seed_data["super_user_id"], "superadmin")
    response = client.put(
        f"/api/v1/superadmin/users/{seed_data['admin_user_id']}/change-role",
        headers=headers,
        json={"id_role": 999999},
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid role specified"


def test_change_role_non_admin_role_rejected(client, app, seed_data):
    """PUT change-role rejects role outside administrator/superadmin."""
    headers = _auth_headers(app, seed_data["super_user_id"], "superadmin")
    response = client.put(
        f"/api/v1/superadmin/users/{seed_data['admin_user_id']}/change-role",
        headers=headers,
        json={"id_role": seed_data["role_guest_id"]},
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "Role must be administrator or superadmin"


def test_reset_password_user_not_found(client, app, seed_data):
    """POST reset-password returns 404 when user is missing."""
    headers = _auth_headers(app, seed_data["super_user_id"], "superadmin")
    response = client.post(
        "/api/v1/superadmin/users/999999/reset-password",
        headers=headers,
        json={"password": "Strongpass123"},
    )
    assert response.status_code == 404
    assert response.get_json()["error"] == "User not found"


def test_create_association_user_not_found(client, app, seed_data):
    """POST associations returns 404 for unknown user."""
    headers = _auth_headers(app, seed_data["super_user_id"], "superadmin")
    response = client.post(
        "/api/v1/superadmin/associations",
        headers=headers,
        json={"user_id": 999999, "structure_id": seed_data["structure_a_id"]},
    )
    assert response.status_code == 404
    assert response.get_json()["error"] == "User not found"


def test_create_association_structure_not_found(client, app, seed_data):
    """POST associations returns 404 for unknown structure."""
    headers = _auth_headers(app, seed_data["super_user_id"], "superadmin")
    response = client.post(
        "/api/v1/superadmin/associations",
        headers=headers,
        json={"user_id": seed_data["admin_user_id"], "structure_id": 999999},
    )
    assert response.status_code == 404
    assert response.get_json()["error"] == "Structure not found"


def test_create_association_duplicate_rejected(client, app, seed_data):
    """POST associations rejects duplicate user-structure mapping."""
    headers = _auth_headers(app, seed_data["super_user_id"], "superadmin")
    response = client.post(
        "/api/v1/superadmin/associations",
        headers=headers,
        json={"user_id": seed_data["admin_user_id"], "structure_id": seed_data["structure_a_id"]},
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "Association already exists"


def test_delete_association_not_found(client, app, seed_data):
    """DELETE associations returns 404 if mapping does not exist."""
    headers = _auth_headers(app, seed_data["super_user_id"], "superadmin")
    response = client.delete(
        "/api/v1/superadmin/associations",
        headers=headers,
        json={"user_id": seed_data["admin_user_2_id"], "structure_id": seed_data["structure_b_id"]},
    )
    assert response.status_code == 404
    assert response.get_json()["error"] == "Association not found"


def test_dashboard_requires_superadmin_role(client, app, seed_data):
    """GET dashboard rejects administrator role."""
    headers = _auth_headers(app, seed_data["admin_user_id"], "administrator")
    response = client.get("/api/v1/superadmin/dashboard", headers=headers)
    assert response.status_code == 403
    assert "error" in response.get_json()
