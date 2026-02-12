"""Failure-path tests for Portale Alloggi admin endpoints."""

# pylint: disable=redefined-outer-name,missing-class-docstring,missing-function-docstring,too-few-public-methods

from uuid import uuid4

from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
import pytest
from sqlalchemy import text

from models import Role, User
from routes import admin_routes
from routes.admin_routes import admin_bp
from utils.encryption_utils import encrypt_password
from database import Base, SessionLocal, engine


@pytest.fixture(scope="module")
def app():
    """Create test app with admin routes only."""
    flask_app = Flask(__name__)
    flask_app.config.from_object("config.TestConfig")
    flask_app.config["JWT_SECRET_KEY"] = "test-secret"
    flask_app.config["JWT_TOKEN_LOCATION"] = ["headers"]
    JWTManager(flask_app)
    flask_app.register_blueprint(admin_bp)
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
def admin_user_with_portale_creds(app):
    """Create an admin user with configured Portale credentials."""
    db = SessionLocal()
    db.query(User).delete()
    db.query(Role).delete()
    db.commit()

    role = Role(name="administrator")
    db.add(role)
    db.commit()
    db.refresh(role)

    suffix = uuid4().hex[:8]
    with app.app_context():
        encrypted_password = encrypt_password("Password123")

    user = User(
        username=f"portale-fail-{suffix}",
        password="hashed",
        id_role=role.id,
        email=f"portale-fail-{suffix}@example.com",
        portale_username=f"user-{suffix}",
        portale_password=encrypted_password,
        portale_wskey=f"wskey-{suffix}",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    user_id = user.id
    db.close()

    yield user_id

    db = SessionLocal()
    db.query(User).filter(User.id == user_id).delete()
    db.commit()
    db.close()


def _headers(app, user_id: int) -> dict:
    """Build admin JWT header."""
    with app.app_context():
        token = create_access_token(identity=str(user_id), additional_claims={"role": "administrator"})
    return {"Authorization": f"Bearer {token}"}


def test_portale_test_authenticate_returns_none(client, app, admin_user_with_portale_creds, monkeypatch):
    """When service authenticate returns None, endpoint should return 400 contract."""
    class FakeService:
        def __init__(self, username, password, ws_key):
            self.username = username
            self.password = password
            self.ws_key = ws_key

        def authenticate(self):
            return None

    monkeypatch.setattr(admin_routes, "PortaleAlloggiService", FakeService)

    response = client.post(
        "/api/v1/admin/portale-alloggi/test",
        headers=_headers(app, admin_user_with_portale_creds),
        json={},
    )
    assert response.status_code == 400
    payload = response.get_json()
    assert payload["error"] == "Portale Alloggi authentication failed"
    assert payload["status"] == "error"


def test_portale_test_service_raises_exception(client, app, admin_user_with_portale_creds, monkeypatch):
    """When service raises, endpoint should return controlled 400 error payload."""
    class FakeService:
        def __init__(self, username, password, ws_key):
            self.username = username
            self.password = password
            self.ws_key = ws_key

        def authenticate(self):
            raise RuntimeError("boom")

    monkeypatch.setattr(admin_routes, "PortaleAlloggiService", FakeService)

    response = client.post(
        "/api/v1/admin/portale-alloggi/test",
        headers=_headers(app, admin_user_with_portale_creds),
        json={},
    )
    assert response.status_code == 400
    payload = response.get_json()
    assert payload["error"] == "Portale Alloggi connection failed"
    assert payload["status"] == "error"


def test_portale_test_decrypt_failure_returns_500(client, app, admin_user_with_portale_creds, monkeypatch):
    """Decrypt failure should be handled by generic database/error contract path."""
    def _raise_decrypt(_):
        raise ValueError("invalid encrypted payload")

    monkeypatch.setattr(admin_routes, "decrypt_password", _raise_decrypt)

    response = client.post(
        "/api/v1/admin/portale-alloggi/test",
        headers=_headers(app, admin_user_with_portale_creds),
        json={},
    )
    assert response.status_code == 500
    payload = response.get_json()
    # handle_database_error uses {"message": ...}
    assert "message" in payload
