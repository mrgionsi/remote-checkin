"""Pagination and filtering edge-case tests for superadmin list endpoints."""

# pylint: disable=redefined-outer-name

from uuid import uuid4

from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
import pytest
from sqlalchemy import text

from models import AdminStructure, Reservation, Role, Room, Structure, User
from routes.superadmin_routes import superadmin_bp
from database import Base, SessionLocal, engine


@pytest.fixture(scope="module")
def app():
    """Create test app with superadmin routes."""
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
    """Seed roles/users/structures for pagination tests."""
    db = SessionLocal()
    db.query(AdminStructure).delete()
    db.query(Reservation).delete()
    db.query(Room).delete()
    db.query(Structure).delete()
    db.query(User).delete()
    db.query(Role).delete()
    db.commit()

    super_role = Role(name="superadmin")
    admin_role = Role(name="administrator")
    db.add_all([super_role, admin_role])
    db.commit()
    db.refresh(super_role)
    db.refresh(admin_role)

    suffix = uuid4().hex[:8]
    super_user = User(
        username=f"sup-pg-{suffix}",
        password="hashed",
        id_role=super_role.id,
        email=f"sup-pg-{suffix}@example.com",
    )
    db.add(super_user)

    admins = []
    for idx in range(3):
        user = User(
            username=f"adm-pg-{idx}-{suffix}",
            password="hashed",
            id_role=admin_role.id,
            email=f"adm-pg-{idx}-{suffix}@example.com",
            name=f"Admin{idx}",
            surname="Tester",
        )
        admins.append(user)
        db.add(user)

    structures = []
    for idx in range(4):
        structure = Structure(
            name=f"EdgeStruct{idx}-{suffix}",
            city="Rome" if idx % 2 == 0 else "Milan",
            street=f"Street {idx}",
            is_active=(idx % 2 == 0),
        )
        structures.append(structure)
        db.add(structure)

    db.commit()
    db.refresh(super_user)
    for user in admins:
        db.refresh(user)
    for structure in structures:
        db.refresh(structure)

    yield {
        "super_user_id": super_user.id,
        "sample_structure_name": structures[0].name,
    }
    db.close()


def _headers(app, user_id: int, role: str) -> dict:
    """Build auth headers."""
    with app.app_context():
        token = create_access_token(identity=str(user_id), additional_claims={"role": role})
    return {"Authorization": f"Bearer {token}"}


def test_structures_per_page_is_capped_to_100(client, app, seed_data):
    """GET structures should cap per_page to 100."""
    headers = _headers(app, seed_data["super_user_id"], "superadmin")
    response = client.get("/api/v1/superadmin/structures?per_page=999", headers=headers)
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["pagination"]["per_page"] == 100


def test_structures_search_with_no_matches_returns_empty(client, app, seed_data):
    """GET structures should return empty result when search has no matches."""
    headers = _headers(app, seed_data["super_user_id"], "superadmin")
    response = client.get("/api/v1/superadmin/structures?search=__not_found__", headers=headers)
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["structures"] == []
    assert payload["pagination"]["total"] == 0


def test_structures_invalid_is_active_filter_does_not_crash(client, app, seed_data):
    """GET structures should ignore unknown is_active values and still return 200."""
    headers = _headers(app, seed_data["super_user_id"], "superadmin")
    response = client.get("/api/v1/superadmin/structures?is_active=definitely-not-bool", headers=headers)
    assert response.status_code == 200
    payload = response.get_json()
    assert "structures" in payload
    assert "pagination" in payload


def test_users_unknown_role_filter_returns_empty(client, app, seed_data):
    """GET users with an unknown role filter should return empty set."""
    headers = _headers(app, seed_data["super_user_id"], "superadmin")
    response = client.get("/api/v1/superadmin/users?role=unknown-role", headers=headers)
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["users"] == []
