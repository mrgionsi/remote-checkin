"""Security tests for reservation upload token validation."""

# pylint: disable=redefined-outer-name

from io import BytesIO
import time

import pytest
from flask import Flask
from itsdangerous import URLSafeTimedSerializer

from extensions import limiter
from routes.upload_reservation_routes import (
    upload_bp,
    UPLOAD_TOKEN_SALT,
)

# pylint: disable=all


def _multipart_payload(token=None):
    """Build a multipart payload with required upload fields."""
    data = {
        "reservationId": "RES-SEC-001",
        "name": "John",
        "surname": "Doe",
        "birthday": "1990-01-01",
        "street": "Main St",
        "number_city": "10",
        "cap": "00100",
        "telephone": "123456789",
        "document_type": "ID",
        "document_number": "A1234567",
        "cf": "DOEJHN90A01H501X",
        "sesso": "1",
        "nazionalita": "IT",
        "email": "john@example.com",
        "comune_nascita": "Roma",
        "provincia_nascita": "RM",
        "stato_nascita": "Italia",
        "cittadinanza": "Italia",
        "luogo_emissione": "Roma",
        "data_emissione": "2020-01-01",
        "data_scadenza": "2030-01-01",
        "autorita_rilascio": "Comune",
        "comune_residenza": "Roma",
        "provincia_residenza": "RM",
        "stato_residenza": "Italia",
        "frontimage": (BytesIO(b"front"), "front.jpg"),
        "backimage": (BytesIO(b"back"), "back.jpg"),
        "selfie": (BytesIO(b"selfie"), "selfie.jpg"),
    }
    if token:
        data["uploadToken"] = token
    return data


@pytest.fixture()
def app():
    """Create a minimal Flask app configured for upload route tests."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = "test-secret"
    app.config["RATELIMIT_ENABLED"] = False
    app.register_blueprint(upload_bp)
    limiter.init_app(app)
    return app


@pytest.fixture()
def client(app):
    """Return the Flask test client."""
    return app.test_client()


def test_upload_rejects_missing_token(client):
    """Reject upload requests without a token."""
    response = client.post(
        "/api/v1/upload",
        data=_multipart_payload(),
        content_type="multipart/form-data",
    )
    assert response.status_code == 401
    assert response.get_json()["error"] == "Missing upload token"


def test_upload_rejects_invalid_token(client):
    """Reject upload requests with a malformed token."""
    response = client.post(
        "/api/v1/upload",
        data=_multipart_payload(token="invalid-token"),
        content_type="multipart/form-data",
    )
    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid upload token"


def test_upload_rejects_expired_token(client, monkeypatch):
    """Reject upload requests when token age exceeds max_age."""
    # Keep this test deterministic by forcing a short max_age.
    monkeypatch.setattr(
        "routes.upload_reservation_routes.UPLOAD_TOKEN_MAX_AGE_SECONDS",
        1,
    )
    serializer = URLSafeTimedSerializer("test-secret")
    token = serializer.dumps({"reservation_ref": "RES-SEC-001"}, salt=UPLOAD_TOKEN_SALT)
    time.sleep(2.0)
    response = client.post(
        "/api/v1/upload",
        data=_multipart_payload(token=token),
        content_type="multipart/form-data",
    )
    assert response.status_code == 401
    assert response.get_json()["error"] == "Upload token expired"
