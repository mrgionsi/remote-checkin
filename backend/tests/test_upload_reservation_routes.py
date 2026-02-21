import pytest
from io import BytesIO
from flask import Flask
from pathlib import Path
from sqlalchemy import text
from itsdangerous import URLSafeTimedSerializer
from routes.upload_reservation_routes import upload_bp
from extensions import limiter
from database import engine, Base, SessionLocal
from models import Reservation, ClientReservations
from routes.upload_reservation_routes import UPLOAD_TOKEN_SALT

# Disable pylint warnings
# pylint: disable=all
TEST_IMAGES_DIR = Path(__file__).resolve().parent / "test_images"

@pytest.fixture(scope="module")
def app():
    """
    Create and configure a Flask application for testing.
    """
    app = Flask(__name__)
    app.config.from_object("config.TestConfig")
    app.config["JWT_SECRET_KEY"] = "test-secret"
    app.register_blueprint(upload_bp)
    limiter.init_app(app)
    Base.metadata.create_all(bind=engine)
    yield app
    with engine.connect() as conn:
        try:
            conn.execute(text("DROP VIEW IF EXISTS structure_reservations CASCADE"))
        except Exception:
            pass
        try:
            conn.execute(text("DROP TABLE IF EXISTS structure_reservations CASCADE"))
        except Exception:
            pass
        conn.commit()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(app):
    """
    Return a test client for simulating API requests on a Flask application.
    """
    return app.test_client()


@pytest.fixture(autouse=True)
def mock_ocr_validation(monkeypatch):
    """Avoid dependence on local tesseract binary for route tests."""
    monkeypatch.setattr(
        "routes.upload_reservation_routes.validate_document",
        lambda *_: {
            "valid": True,
            "error": "",
            "extracted_text": "Valid OCR text",
            "confidence": 80.0,
            "variant": "gray",
        },
    )


def _build_upload_token(app, reservation_reference: str):
    serializer = URLSafeTimedSerializer(app.config["JWT_SECRET_KEY"])
    return serializer.dumps({"reservation_ref": reservation_reference}, salt=UPLOAD_TOKEN_SALT)


def _base_upload_form(reservation_id: str, token: str):
    return {
        "reservationId": reservation_id,
        "uploadToken": token,
        "name": "John",
        "surname": "Doe",
        "birthday": "1990-01-01",
        "street": "123 Main St",
        "number_city": "10",
        "cap": "12345",
        "telephone": "1234567890",
        "document_type": "ID",
        "document_number": "ABC123456",
        "cf": "JHNDOE90A01X123Y",
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
        "autorita_rilascio": "Questura",
        "comune_residenza": "Roma",
        "provincia_residenza": "RM",
        "stato_residenza": "Italia",
    }

@pytest.fixture
def init_db():
    """
    Initialize the test database with a sample reservation.
    """
    db = SessionLocal()
    reservation = Reservation(
        id_reference="12345",
        start_date="2024-06-01",
        end_date="2024-06-10",
        email="guest@example.com"
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    yield db
    db.query(ClientReservations).filter_by(id_reservation=reservation.id).delete()
    db.query(Reservation).filter_by(id_reference="12345").delete()
    db.commit()
    db.close()

def test_successful_upload(client, init_db):
    """Test successful document upload."""
    token = _build_upload_token(client.application, "12345")
    with open(TEST_IMAGES_DIR / "front.jpeg", 'rb') as front_file, \
         open(TEST_IMAGES_DIR / "back.jpeg", 'rb') as back_file, \
         open(TEST_IMAGES_DIR / "selfie.jpeg", 'rb') as selfie_file:
        data = _base_upload_form("12345", token)
        data["frontimage"] = (front_file, "front.jpeg", "image/jpeg")
        data["backimage"] = (back_file, "back.jpeg", "image/jpeg")
        data["selfie"] = (selfie_file, "selfie.jpeg", "image/jpeg")

        response = client.post(
            "/api/v1/upload",
            data=data,
            content_type='multipart/form-data'
        )

        assert response.status_code == 200


def test_upload_missing_files(client):
    """
    Test upload with missing files.
    """
    data = {"reservationId": "12345"}
    response = client.post("/api/v1/upload", data=data)
    assert response.status_code == 400
    assert response.get_json()["error"] == "Missing one or more required image files"


##Even pdf files can be uploaded
#def test_upload_invalid_file_type(client):
#    """
#    Test upload with an invalid file type.
#    """
#    data = {"reservationId": "12345", "frontimage": (BytesIO(b"fake data"), "document.pdf")}
#    response = client.post("/api/v1/upload", data=data, content_type='multipart/form-data')
#    assert response.status_code == 400
#    assert "Invalid file type" in response.get_json()["error"]

def test_upload_nonexistent_reservation(client):
    """
    Test upload with a nonexistent reservation.
    """
    token = _build_upload_token(client.application, "99999")
    with open(TEST_IMAGES_DIR / "front.jpeg", 'rb') as front_file, \
         open(TEST_IMAGES_DIR / "back.jpeg", 'rb') as back_file, \
         open(TEST_IMAGES_DIR / "selfie.jpeg", 'rb') as selfie_file:
        data = _base_upload_form("99999", token)
        data["frontimage"] = (front_file, "front.jpeg", "image/jpeg")
        data["backimage"] = (back_file, "back.jpeg", "image/jpeg")
        data["selfie"] = (selfie_file, "selfie.jpeg", "image/jpeg")
        response = client.post("/api/v1/upload", data=data, content_type='multipart/form-data')
        assert response.status_code == 404
        assert "Reservation not found" in response.get_json()["error"]


def test_upload_invalid_gender_returns_validation_error(client):
    """Validation: invalid gender value should return a 400 with safe error payload."""
    token = _build_upload_token(client.application, "12345")
    with open(TEST_IMAGES_DIR / "front.jpeg", "rb") as front_file, \
         open(TEST_IMAGES_DIR / "back.jpeg", "rb") as back_file, \
         open(TEST_IMAGES_DIR / "selfie.jpeg", "rb") as selfie_file:
        data = _base_upload_form("12345", token)
        data["sesso"] = "9"
        data["frontimage"] = (front_file, "front.jpeg", "image/jpeg")
        data["backimage"] = (back_file, "back.jpeg", "image/jpeg")
        data["selfie"] = (selfie_file, "selfie.jpeg", "image/jpeg")
        response = client.post("/api/v1/upload", data=data, content_type="multipart/form-data")

    assert response.status_code == 400
    payload = response.get_json()
    assert "error" in payload
    assert "Traceback" not in payload["error"]


def test_validate_documents_success_returns_token(client, init_db):
    """Pre-validation should return a reusable validation token."""
    token = _build_upload_token(client.application, "12345")
    with open(TEST_IMAGES_DIR / "front.jpeg", "rb") as front_file, \
         open(TEST_IMAGES_DIR / "back.jpeg", "rb") as back_file, \
         open(TEST_IMAGES_DIR / "selfie.jpeg", "rb") as selfie_file:
        data = {
            "reservationId": "12345",
            "frontimage": (front_file, "front.jpeg", "image/jpeg"),
            "backimage": (back_file, "back.jpeg", "image/jpeg"),
            "selfie": (selfie_file, "selfie.jpeg", "image/jpeg"),
        }
        response = client.post(
            "/api/v1/upload/validate-documents",
            data=data,
            content_type="multipart/form-data",
            headers={"X-Upload-Token": token},
        )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["message"] == "Document validation successful"
    assert "document_validation_token" in payload


def test_validate_documents_invalid_returns_422(client, init_db, monkeypatch):
    """Pre-validation should report invalid files without saving client data."""
    monkeypatch.setattr(
        "routes.upload_reservation_routes.validate_document",
        lambda *_: {
            "valid": False,
            "error": "No valid text detected",
            "extracted_text": "",
            "confidence": 12.0,
            "variant": "gray",
        },
    )
    token = _build_upload_token(client.application, "12345")
    with open(TEST_IMAGES_DIR / "front.jpeg", "rb") as front_file, \
         open(TEST_IMAGES_DIR / "back.jpeg", "rb") as back_file, \
         open(TEST_IMAGES_DIR / "selfie.jpeg", "rb") as selfie_file:
        data = {
            "reservationId": "12345",
            "frontimage": (front_file, "front.jpeg", "image/jpeg"),
            "backimage": (back_file, "back.jpeg", "image/jpeg"),
            "selfie": (selfie_file, "selfie.jpeg", "image/jpeg"),
        }
        response = client.post(
            "/api/v1/upload/validate-documents",
            data=data,
            content_type="multipart/form-data",
            headers={"X-Upload-Token": token},
        )

    assert response.status_code == 422
    payload = response.get_json()
    assert payload["retryable"] is True
    assert payload["invalid_files"][0]["field"] == "frontimage"


def test_upload_with_document_validation_token_skips_ocr(client, init_db, monkeypatch):
    """Final upload should accept prevalidated token and skip OCR pass."""
    token = _build_upload_token(client.application, "12345")
    with open(TEST_IMAGES_DIR / "front.jpeg", "rb") as front_file, \
         open(TEST_IMAGES_DIR / "back.jpeg", "rb") as back_file, \
         open(TEST_IMAGES_DIR / "selfie.jpeg", "rb") as selfie_file:
        validation_data = {
            "reservationId": "12345",
            "frontimage": (front_file, "front.jpeg", "image/jpeg"),
            "backimage": (back_file, "back.jpeg", "image/jpeg"),
            "selfie": (selfie_file, "selfie.jpeg", "image/jpeg"),
        }
        validate_resp = client.post(
            "/api/v1/upload/validate-documents",
            data=validation_data,
            content_type="multipart/form-data",
            headers={"X-Upload-Token": token},
        )

    assert validate_resp.status_code == 200
    validation_token = validate_resp.get_json()["document_validation_token"]

    calls = {"count": 0}

    def failing_ocr(*_args, **_kwargs):
        calls["count"] += 1
        return {"valid": False, "error": "Should not run", "confidence": 0.0, "variant": None, "extracted_text": ""}

    monkeypatch.setattr("routes.upload_reservation_routes.validate_document", failing_ocr)

    with open(TEST_IMAGES_DIR / "front.jpeg", "rb") as front_file, \
         open(TEST_IMAGES_DIR / "back.jpeg", "rb") as back_file, \
         open(TEST_IMAGES_DIR / "selfie.jpeg", "rb") as selfie_file:
        data = _base_upload_form("12345", token)
        data["frontimage"] = (front_file, "front.jpeg", "image/jpeg")
        data["backimage"] = (back_file, "back.jpeg", "image/jpeg")
        data["selfie"] = (selfie_file, "selfie.jpeg", "image/jpeg")
        response = client.post(
            "/api/v1/upload",
            data=data,
            content_type="multipart/form-data",
            headers={"X-Upload-Token": token, "X-Document-Validation-Token": validation_token},
        )

    assert response.status_code == 200
    assert calls["count"] == 0


def test_upload_without_validation_token_returns_422_on_ocr_failure(client, init_db, monkeypatch):
    """Final upload should fail when OCR fails and no prevalidation token is supplied."""
    monkeypatch.setattr(
        "routes.upload_reservation_routes.validate_document",
        lambda *_: {
            "valid": False,
            "error": "No valid text detected",
            "extracted_text": "",
            "confidence": 5.0,
            "variant": "gray",
        },
    )
    token = _build_upload_token(client.application, "12345")
    with open(TEST_IMAGES_DIR / "front.jpeg", "rb") as front_file, \
         open(TEST_IMAGES_DIR / "back.jpeg", "rb") as back_file, \
         open(TEST_IMAGES_DIR / "selfie.jpeg", "rb") as selfie_file:
        data = _base_upload_form("12345", token)
        data["frontimage"] = (front_file, "front.jpeg", "image/jpeg")
        data["backimage"] = (back_file, "back.jpeg", "image/jpeg")
        data["selfie"] = (selfie_file, "selfie.jpeg", "image/jpeg")
        response = client.post(
            "/api/v1/upload",
            data=data,
            content_type="multipart/form-data",
            headers={"X-Upload-Token": token},
        )

    assert response.status_code == 422
    payload = response.get_json()
    assert payload["retryable"] is True
    assert payload["invalid_files"][0]["field"] == "frontimage"


def test_upload_invalid_file_signature_returns_validation_error(client, init_db):
    """Validation: spoofed non-image payload should return 400."""
    token = _build_upload_token(client.application, "12345")
    with open(TEST_IMAGES_DIR / "back.jpeg", "rb") as back_file, \
         open(TEST_IMAGES_DIR / "selfie.jpeg", "rb") as selfie_file:
        data = _base_upload_form("12345", token)
        data["frontimage"] = (BytesIO(b"not-an-image"), "front.jpeg", "image/jpeg")
        data["backimage"] = (back_file, "back.jpeg", "image/jpeg")
        data["selfie"] = (selfie_file, "selfie.jpeg", "image/jpeg")
        response = client.post("/api/v1/upload", data=data, content_type="multipart/form-data")

    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid MIME type for frontimage"


def test_upload_oversized_file_returns_validation_error(client, init_db, monkeypatch):
    """Validation: oversized image should be rejected before OCR processing."""
    monkeypatch.setattr("routes.upload_reservation_routes.MAX_UPLOAD_FILE_SIZE_BYTES", 32)
    token = _build_upload_token(client.application, "12345")
    data = _base_upload_form("12345", token)
    data["frontimage"] = (BytesIO(b"\xff\xd8\xff" + b"x" * 128), "front.jpeg", "image/jpeg")
    data["backimage"] = (BytesIO(b"\xff\xd8\xff" + b"ok"), "back.jpeg", "image/jpeg")
    data["selfie"] = (BytesIO(b"\xff\xd8\xff" + b"ok"), "selfie.jpeg", "image/jpeg")

    response = client.post("/api/v1/upload", data=data, content_type="multipart/form-data")

    assert response.status_code == 400
    assert response.get_json()["error"] == "File too large for frontimage"
