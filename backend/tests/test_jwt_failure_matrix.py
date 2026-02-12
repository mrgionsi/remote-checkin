"""JWT failure matrix tests for protected backend endpoints."""

# pylint: disable=redefined-outer-name

from flask import Flask
from flask_jwt_extended import JWTManager
import pytest

from routes.admin_routes import admin_bp
from routes.reservation_routes import reservation_bp
from routes.room_routes import room_bp
from routes.superadmin_routes import superadmin_bp


@pytest.fixture(scope="module")
def app():
    """Create a Flask app with protected blueprints and JWT configured."""
    flask_app = Flask(__name__)
    flask_app.config["TESTING"] = True
    flask_app.config["JWT_SECRET_KEY"] = "test-secret"
    flask_app.config["JWT_TOKEN_LOCATION"] = ["headers"]
    JWTManager(flask_app)
    flask_app.register_blueprint(room_bp)
    flask_app.register_blueprint(reservation_bp)
    flask_app.register_blueprint(admin_bp)
    flask_app.register_blueprint(superadmin_bp)
    return flask_app


@pytest.fixture()
def client(app):
    """Return Flask test client."""
    return app.test_client()


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/api/v1/rooms"),
        ("get", "/api/v1/reservations/monthly/1"),
        ("get", "/api/v1/admin/me"),
        ("get", "/api/v1/superadmin/dashboard"),
    ],
)
def test_protected_routes_reject_missing_jwt(client, method, path):
    """Protected routes should reject missing JWT with 401."""
    response = getattr(client, method)(path)
    assert response.status_code == 401
    payload = response.get_json()
    assert payload is not None
    assert "msg" in payload


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/api/v1/rooms"),
        ("get", "/api/v1/reservations/monthly/1"),
        ("get", "/api/v1/admin/me"),
        ("get", "/api/v1/superadmin/dashboard"),
    ],
)
def test_protected_routes_reject_invalid_jwt(client, method, path):
    """Protected routes should reject malformed JWT with 422/401."""
    response = getattr(client, method)(
        path,
        headers={"Authorization": "Bearer invalid.token.value"},
    )
    assert response.status_code in (401, 422)
    payload = response.get_json()
    assert payload is not None
    # flask-jwt-extended emits "msg" for decode/auth header failures
    assert "msg" in payload
