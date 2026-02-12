"""Validation and error-contract tests for admin Portale Alloggi endpoints."""

# pylint: disable=redefined-outer-name

from uuid import uuid4

import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

from models import Role, User
from routes.admin_routes import PORTALE_CREDENTIALS_NOT_CONFIGURED, USER_NOT_FOUND, admin_bp
from database import Base, SessionLocal, engine


@pytest.fixture(scope="module")
def app():
    """Create a Flask app for admin Portale Alloggi route tests."""
    flask_app = Flask(__name__)
    flask_app.config["TESTING"] = True
    flask_app.config["JWT_SECRET_KEY"] = "test-secret"
    flask_app.config["JWT_TOKEN_LOCATION"] = ["headers"]
    JWTManager(flask_app)
    flask_app.register_blueprint(admin_bp)
    Base.metadata.create_all(bind=engine)
    yield flask_app


@pytest.fixture()
def client(app):
    """Return Flask test client."""
    return app.test_client()


def _auth_headers(app, identity: str, role: str) -> dict:
    """Build JWT auth header."""
    with app.app_context():
        token = create_access_token(identity=identity, additional_claims={"role": role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_user():
    """Create an administrator user without Portale Alloggi credentials configured."""
    db = SessionLocal()
    unique = uuid4().hex[:8]
    username = f"portale-admin-{unique}"
    email = f"portale-admin-{unique}@example.com"

    role = db.query(Role).filter(Role.name == "administrator").first()
    if role is None:
        role = Role(name="administrator")
        db.add(role)
        db.commit()
        db.refresh(role)

    user = User(
        username=username,
        password="hashed",
        name="Portale",
        surname="Admin",
        email=email,
        id_role=role.id,
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


def test_portale_get_requires_auth(client):
    """GET /admin/portale-alloggi rejects missing auth token."""
    response = client.get("/api/v1/admin/portale-alloggi")
    assert response.status_code == 401
    assert "msg" in response.get_json()


def test_portale_get_requires_admin_role(client, app):
    """GET /admin/portale-alloggi rejects non-admin roles."""
    headers = _auth_headers(app, identity="111", role="guest")
    response = client.get("/api/v1/admin/portale-alloggi", headers=headers)
    assert response.status_code == 403
    payload = response.get_json()
    assert "error" in payload
    assert "administrator" in payload["error"].lower()


def test_portale_update_requires_non_empty_payload(client, app):
    """POST /admin/portale-alloggi validates missing/empty JSON payload."""
    headers = _auth_headers(app, identity="111", role="administrator")
    response = client.post("/api/v1/admin/portale-alloggi", headers=headers, json={})
    assert response.status_code == 400
    assert response.get_json()["error"] == "No data provided"


def test_portale_update_user_not_found_returns_404(client, app):
    """POST /admin/portale-alloggi returns 404 for unknown JWT user."""
    headers = _auth_headers(app, identity="999999", role="administrator")
    response = client.post(
        "/api/v1/admin/portale-alloggi",
        headers=headers,
        json={"portale_username": "x"},
    )
    assert response.status_code == 404
    assert response.get_json()["error"] == USER_NOT_FOUND


def test_portale_test_credentials_not_configured_returns_400(client, app, admin_user):
    """POST /admin/portale-alloggi/test returns explicit credentials-not-configured error."""
    headers = _auth_headers(app, identity=str(admin_user), role="administrator")
    response = client.post("/api/v1/admin/portale-alloggi/test", headers=headers, json={})
    assert response.status_code == 400
    payload = response.get_json()
    assert payload["error"] == PORTALE_CREDENTIALS_NOT_CONFIGURED
    assert "details" in payload
