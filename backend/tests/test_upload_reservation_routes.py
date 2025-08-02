import pytest
from flask import Flask
from sqlalchemy import text
from routes.upload_reservation_routes import upload_bp
from database import engine, Base, SessionLocal
from models import Reservation

# Disable pylint warnings
# pylint: disable=all

@pytest.fixture(scope="module")
def app():
    """
    Create and configure a Flask application for testing.
    """
    app = Flask(__name__)
    app.config.from_object("config.TestConfig")
    app.register_blueprint(upload_bp)
    Base.metadata.create_all(bind=engine)
    yield app
    #with engine.connect() as conn:
    #    conn.execute(text("DROP VIEW IF EXISTS structure_reservations"))
    #    conn.execute(text("ALTER TABLE IF EXISTS reservation DROP CONSTRAINT IF EXISTS fk_reservation_client CASCADE"))

    #Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(app):
    """
    Return a test client for simulating API requests on a Flask application.
    """
    return app.test_client()

@pytest.fixture
def init_db():
    """
    Initialize the test database with a sample reservation.
    """
    db = SessionLocal()
    reservation = Reservation(id_reference="12345", start_date="2024-06-01", end_date="2024-06-10")
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    yield db
    db.close()

def test_successful_upload(client, init_db):
    """Test successful document upload."""
    with open("tests/test_images/front.jpeg", 'rb') as front_file, \
         open("tests/test_images/back.jpeg", 'rb') as back_file, \
         open("tests/test_images/selfie.jpeg", 'rb') as selfie_file:
        data = {
            "reservationId": "12345",
            "name": "John",
            "surname": "Doe",
            "birthday": "1990-01-01",
            "street": "123 Main St",
            "city": "Test City",
            "province": "Test Province",
            "cap": "12345",
            "telephone": "1234567890",
            "document_type": "ID",
            "document_number": "ABC123456",
            "cf": "JHNDOE90A01X123Y",
            "frontimage": (
                front_file,
                "front.jpeg",
                "image/jpeg"
            ),
            "backimage": (
                back_file,
                "back.jpeg",
                "image/jpeg"
            ),
            "selfie": (
                selfie_file,
                "selfie.jpeg",
                "image/jpeg"
            )
        }

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
    assert "Missing one or more required image files" in response.get_json()["error"]


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
    with open("tests/test_images/front.jpeg", 'rb') as front_file, \
         open("tests/test_images/back.jpeg", 'rb') as back_file, \
         open("tests/test_images/selfie.jpeg", 'rb') as selfie_file:
        data = {
            "reservationId": "99999",
            "name": "John",
            "surname": "Doe",
            "birthday": "1990-01-01",
            "street": "123 Main St",
            "city": "Test City",
            "province": "Test Province",
            "cap": "12345",
            "telephone": "1234567890",
            "document_type": "ID",
            "document_number": "ABC123456",
            "cf": "JHNDOE90A01X123Y",
            "frontimage": (
                front_file,
                "front.jpeg",
                "image/jpeg"
            ),
            "backimage": (
                back_file,
                "back.jpeg",
                "image/jpeg"
            ),
            "selfie": (
                selfie_file,
                "selfie.jpeg",
                "image/jpeg"
            )
        }
        response = client.post("/api/v1/upload", data=data, content_type='multipart/form-data')
        print(response.json)
        assert response.status_code == 404
        assert "Reservation not found" in response.get_json()["error"]
