import pytest
from flask import Flask
from pathlib import Path
from sqlalchemy import text
from itsdangerous import URLSafeTimedSerializer
from routes.upload_reservation_routes import upload_bp
from database import engine, Base, SessionLocal
from models import Reservation
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

        print("PRINTING ", response.json)  # Debugging

        assert response.status_code == 200


def test_upload_missing_files(client):
    """
    Test upload with missing files.
    """
    data = {"reservationId": "12345"}
    response = client.post("/api/v1/upload", data=data)
    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid upload request"


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
        print(response.json)
        assert response.status_code == 404
        assert "Reservation not found" in response.get_json()["error"]
