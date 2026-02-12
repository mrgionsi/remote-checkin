"""Database fault contract tests (generic 500 / safe payloads)."""

# pylint: disable=redefined-outer-name

from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
import pytest
from sqlalchemy.exc import SQLAlchemyError

from routes import admin_routes, reservation_routes, superadmin_routes
from routes.admin_routes import admin_bp
from routes.reservation_routes import reservation_bp
from routes.superadmin_routes import superadmin_bp


class _FailingSession:
    """Minimal session stub that raises SQLAlchemyError on DB query usage."""

    def query(self, *args, **kwargs):
        """Raise a DB error for any query call."""
        raise SQLAlchemyError("db down")

    def close(self):
        """No-op close."""

    def rollback(self):
        """No-op rollback."""


@pytest.fixture(scope="module")
def app():
    """Create Flask app for DB-fault contract tests."""
    flask_app = Flask(__name__)
    flask_app.config["TESTING"] = True
    flask_app.config["JWT_SECRET_KEY"] = "test-secret"
    flask_app.config["JWT_TOKEN_LOCATION"] = ["headers"]
    JWTManager(flask_app)
    flask_app.register_blueprint(reservation_bp)
    flask_app.register_blueprint(admin_bp)
    flask_app.register_blueprint(superadmin_bp)
    return flask_app


@pytest.fixture()
def client(app):
    """Return Flask test client."""
    return app.test_client()


def _headers(app, role: str) -> dict:
    """Build auth headers for role-based endpoints."""
    with app.app_context():
        token = create_access_token(identity="1", additional_claims={"role": role})
    return {"Authorization": f"Bearer {token}"}


def test_reservation_structure_db_fault_returns_generic_500(client, app, monkeypatch):
    """Reservation structure endpoint should return safe DB error payload."""
    monkeypatch.setattr(reservation_routes, "SessionLocal", _FailingSession)
    response = client.get(
        "/api/v1/reservations/structure/1",
        headers=_headers(app, "administrator"),
    )
    assert response.status_code == 500
    payload = response.get_json()
    assert payload["error"] == "Database error"
    assert "db down" not in payload["error"].lower()


def test_admin_portale_get_db_fault_returns_generic_500(client, app, monkeypatch):
    """Admin Portale config endpoint should not leak DB exception details."""
    monkeypatch.setattr(admin_routes, "SessionLocal", _FailingSession)
    response = client.get(
        "/api/v1/admin/portale-alloggi",
        headers=_headers(app, "administrator"),
    )
    assert response.status_code == 500
    payload = response.get_json()
    assert "message" in payload
    assert "db down" not in payload["message"].lower()


def test_superadmin_roles_db_fault_returns_generic_500(client, app, monkeypatch):
    """Superadmin roles endpoint should return safe error message on DB failure."""
    monkeypatch.setattr(superadmin_routes, "SessionLocal", _FailingSession)
    response = client.get(
        "/api/v1/superadmin/roles",
        headers=_headers(app, "superadmin"),
    )
    assert response.status_code == 500
    payload = response.get_json()
    assert "message" in payload
    assert "db down" not in payload["message"].lower()
