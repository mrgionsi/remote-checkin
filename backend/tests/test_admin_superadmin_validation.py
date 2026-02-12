"""Validation and error-contract tests for admin and superadmin routes."""

# pylint: disable=redefined-outer-name

import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

from routes.admin_routes import admin_bp
from routes.superadmin_routes import superadmin_bp


@pytest.fixture(scope="module")
def app():
    """Create a minimal Flask app with JWT and admin/superadmin blueprints."""
    flask_app = Flask(__name__)
    flask_app.config["TESTING"] = True
    flask_app.config["JWT_SECRET_KEY"] = "test-secret"
    flask_app.config["JWT_TOKEN_LOCATION"] = ["headers"]
    JWTManager(flask_app)
    flask_app.register_blueprint(admin_bp)
    flask_app.register_blueprint(superadmin_bp)
    return flask_app


@pytest.fixture()
def client(app):
    """Return Flask test client."""
    return app.test_client()


def _auth_headers(app, role: str) -> dict:
    """Build JWT Authorization header for the provided role."""
    with app.app_context():
        token = create_access_token(identity="999", additional_claims={"role": role})
    return {"Authorization": f"Bearer {token}"}


def test_admin_create_requires_auth(client):
    """POST /admin/create should reject missing auth token."""
    response = client.post("/api/v1/admin/create", json={})
    assert response.status_code == 401
    assert "msg" in response.get_json()


def test_admin_create_missing_required_fields(client, app):
    """POST /admin/create validates required fields before DB usage."""
    headers = _auth_headers(app, "administrator")
    response = client.post(
        "/api/v1/admin/create",
        headers=headers,
        json={"username": "user-only"},
    )
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_admin_change_password_requires_json_body(client, app):
    """POST /admin/change-password should return 415 on missing JSON body."""
    headers = _auth_headers(app, "administrator")
    response = client.post("/api/v1/admin/change-password", headers=headers)
    assert response.status_code == 415


def test_admin_change_password_mismatch(client, app):
    """POST /admin/change-password rejects mismatched confirmation."""
    headers = _auth_headers(app, "administrator")
    response = client.post(
        "/api/v1/admin/change-password",
        headers=headers,
        json={
            "current_password": "oldpass123",
            "new_password": "newpass123",
            "confirm_password": "different123",
        },
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "New password and confirmation do not match"


def test_superadmin_create_user_requires_superadmin_role(client, app):
    """POST /superadmin/users should reject administrator role."""
    headers = _auth_headers(app, "administrator")
    response = client.post("/api/v1/superadmin/users", headers=headers, json={})
    assert response.status_code == 403
    assert "error" in response.get_json()


def test_superadmin_create_user_requires_json_body(client, app):
    """POST /superadmin/users should return 400 for missing JSON body."""
    headers = _auth_headers(app, "superadmin")
    response = client.post("/api/v1/superadmin/users", headers=headers)
    assert response.status_code == 415


def test_superadmin_create_user_missing_fields(client, app):
    """POST /superadmin/users validates required user fields."""
    headers = _auth_headers(app, "superadmin")
    response = client.post(
        "/api/v1/superadmin/users",
        headers=headers,
        json={"username": "new-user"},
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "Username, password, name and surname are required"


def test_superadmin_change_role_requires_id_role(client, app):
    """PUT /superadmin/users/<id>/change-role requires id_role in payload."""
    headers = _auth_headers(app, "superadmin")
    response = client.put(
        "/api/v1/superadmin/users/1/change-role",
        headers=headers,
        json={"name": "noop"},
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "id_role is required"


def test_superadmin_reset_password_weak_password(client, app):
    """POST /superadmin/users/<id>/reset-password validates password strength."""
    headers = _auth_headers(app, "superadmin")
    response = client.post(
        "/api/v1/superadmin/users/1/reset-password",
        headers=headers,
        json={"password": "weak"},
    )
    assert response.status_code == 400
    assert "at least 8 characters" in response.get_json()["error"]


def test_superadmin_create_association_missing_fields(client, app):
    """POST /superadmin/associations requires user_id and structure_id."""
    headers = _auth_headers(app, "superadmin")
    response = client.post(
        "/api/v1/superadmin/associations",
        headers=headers,
        json={"user_id": 1},
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "user_id and structure_id are required"
