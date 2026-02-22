"""
Tests for the email handler module.

This module tests the EmailService class and related functionality.
"""
#pylint: disable=C0301,E0611,E0401,W0718,R0914,E0401,C0411,W0212,E1101
from types import SimpleNamespace
from unittest.mock import Mock, patch
import pytest
from flask import Flask
from email_handler import (
    EmailService,
    EmailData,
    EmailValidationError,
    EmailServiceError,
    send_reservation_email
)


class TestEmailData:
    """Test the EmailData dataclass."""

    def test_email_data_creation(self):
        """Test creating EmailData with required fields."""
        email_data = EmailData(
            to_email="test@example.com",
            subject="Test Subject",
            body="Test Body"
        )

        assert email_data.to_email == "test@example.com"
        assert email_data.subject == "Test Subject"
        assert email_data.body == "Test Body"
        assert email_data.html_body is None
        assert email_data.attachments is None
        assert email_data.cc is None
        assert email_data.bcc is None

    def test_email_data_with_optional_fields(self):
        """Test creating EmailData with optional fields."""
        email_data = EmailData(
            to_email="test@example.com",
            subject="Test Subject",
            body="Test Body",
            html_body="<p>Test HTML</p>",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"]
        )

        assert email_data.html_body == "<p>Test HTML</p>"
        assert email_data.cc == ["cc@example.com"]
        assert email_data.bcc == ["bcc@example.com"]


@pytest.fixture(autouse=True)
def flask_app_context():
    """Provide Flask app context so `current_app` LocalProxy is always bound."""
    app = Flask(__name__)
    app.config.update(
        MAIL_SERVER="smtp.example.com",
        MAIL_PORT=587,
        MAIL_USERNAME="test@example.com",
        MAIL_PASSWORD="test_password",  # noqa: S106 - test-only fake secret
        MAIL_DEFAULT_SENDER=("Test Sender", "test@example.com"),
    )
    with app.app_context():
        yield


def _build_email_config(**overrides):
    """Build a minimal EmailConfig-like object for EmailService tests."""
    base = {
        "mail_server": "smtp.example.com",
        "mail_port": 587,
        "mail_use_tls": True,
        "mail_use_ssl": False,
        "mail_username": "test@example.com",
        "mail_password": "plain-password",
        "mail_default_sender_name": "Test Sender",
        "mail_default_sender_email": "test@example.com",
        "provider_type": "smtp",
        "provider_config": None,
        "mail_timeout": 30,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


class TestEmailService:
    """Test the EmailService class."""

    @pytest.fixture
    def email_config(self):
        """Create a mock EmailConfig-like object."""
        return _build_email_config()

    def test_email_service_initialization_success(self, email_config):
        """Test successful EmailService initialization."""
        email_service = EmailService(email_config)
        assert email_service.config == email_config

    def test_email_service_initialization_missing_config(self):
        """Test EmailService initialization with missing config."""
        with pytest.raises(EmailServiceError, match="EmailConfig is required"):
            EmailService(None)

    def test_validate_email_address_valid(self, email_config):
        """Test email address validation with valid email."""
        email_service = EmailService(email_config)
        result = email_service.validate_email_address("test@example.com")
        assert result == "test@example.com"

    def test_validate_email_address_invalid(self, email_config):
        """Test email address validation with invalid email."""
        email_service = EmailService(email_config)

        with pytest.raises(EmailValidationError):
            email_service.validate_email_address("invalid-email")

    def test_validate_email_list_valid(self, email_config):
        """Test email list validation with valid emails."""
        email_service = EmailService(email_config)
        emails = ["test1@example.com", "test2@example.com"]
        result = email_service.validate_email_list(emails)
        assert result == emails

    def test_validate_email_list_invalid(self, email_config):
        """Test email list validation with invalid emails."""
        email_service = EmailService(email_config)
        emails = ["test1@example.com", "invalid-email"]

        with pytest.raises(EmailValidationError, match="Invalid email addresses"):
            email_service.validate_email_list(emails)

    def test_send_email_success(self, email_config):
        """Test successful email sending."""
        email_service = EmailService(email_config)

        email_data = EmailData(
            to_email="test@example.com",
            subject="Test Subject",
            body="Test Body"
        )

        with patch.object(
            EmailService,
            "_send_via_smtp",
            return_value={"status": "success", "message": "Email sent successfully", "to": "test@example.com", "subject": "Test Subject"},
        ) as smtp_mock:
            result = email_service.send_email(email_data)

        assert result["status"] == "success"
        assert result["message"] == "Email sent successfully"
        assert result["to"] == "test@example.com"
        assert result["subject"] == "Test Subject"
        smtp_mock.assert_called_once()

    def test_send_email_validation_error(self, email_config):
        """Test email sending with validation error."""
        email_service = EmailService(email_config)

        email_data = EmailData(
            to_email="invalid-email",
            subject="Test Subject",
            body="Test Body"
        )

        result = email_service.send_email(email_data)

        assert result["status"] == "error"
        assert result["error_type"] in ("validation_error", "send_error")

    def test_send_reservation_confirmation(self, email_config):
        """Test sending reservation confirmation email."""
        email_service = EmailService(email_config)

        reservation_data = {
            'reservation_number': '12345',
            'guest_name': 'John Doe',
            'start_date': '2024-01-01',
            'end_date': '2024-01-03',
            'room_name': 'Deluxe Room'
        }

        with patch.object(EmailService, "send_email", return_value={"status": "success"}) as send_mock:
            result = email_service.send_reservation_confirmation(
                "guest@example.com",
                reservation_data
            )

        assert result["status"] == "success"
        send_mock.assert_called_once()

    def test_send_reservation_update(self, email_config):
        """Test sending reservation update email."""
        email_service = EmailService(email_config)

        reservation_data = {
            'reservation_number': '12345',
            'guest_name': 'John Doe',
            'start_date': '2024-01-01',
            'end_date': '2024-01-05',
            'room_name': 'Suite'
        }

        with patch.object(EmailService, "send_email", return_value={"status": "success"}) as send_mock:
            result = email_service.send_reservation_update(
                "guest@example.com",
                reservation_data
            )

        assert result["status"] == "success"
        send_mock.assert_called_once()

    def test_send_reservation_cancellation(self, email_config):
        """Test sending reservation cancellation email."""
        email_service = EmailService(email_config)

        reservation_data = {
            'reservation_number': '12345',
            'guest_name': 'John Doe',
            'start_date': '2024-01-01',
            'end_date': '2024-01-03',
            'room_name': 'Deluxe Room'
        }

        with patch.object(EmailService, "send_email", return_value={"status": "success"}) as send_mock:
            result = email_service.send_reservation_cancellation(
                "guest@example.com",
                reservation_data
            )

        assert result["status"] == "success"
        send_mock.assert_called_once()

    def test_send_admin_checkin_notification(self, email_config):
        """Test sending admin check-in notification email."""
        email_service = EmailService(email_config)

        checkin_data = {
            'reservation_number': '12345',
            'guest_name': 'John Doe',
            'start_date': '2024-01-01',
            'end_date': '2024-01-03',
            'room_name': 'Deluxe Room',
            'client_name': 'John',
            'client_surname': 'Doe',
            'client_email': 'john@example.com',
            'client_phone': '+1234567890',
            'document_type': 'Passport',
            'document_number': 'AB123456',
            'has_front_image': True,
            'has_back_image': True,
            'has_selfie': True
        }

        with patch.object(EmailService, "send_email", return_value={"status": "success"}) as send_mock:
            result = email_service.send_admin_checkin_notification(
                "admin@example.com",
                checkin_data
            )

        assert result["status"] == "success"
        send_mock.assert_called_once()

    def test_send_reservation_approval_notification(self, email_config):
        """Test sending reservation approval notification email."""
        email_service = EmailService(email_config)

        reservation_data = {
            'reservation_number': '12345',
            'guest_name': 'John Doe',
            'start_date': '2024-01-01',
            'end_date': '2024-01-03',
            'room_name': 'Deluxe Room'
        }

        with patch.object(EmailService, "send_email", return_value={"status": "success"}) as send_mock:
            result = email_service.send_reservation_approval_notification(
                "guest@example.com",
                reservation_data
            )

        assert result["status"] == "success"
        send_mock.assert_called_once()

    def test_send_reservation_revision_notification(self, email_config):
        """Test sending reservation revision notification email."""
        email_service = EmailService(email_config)

        reservation_data = {
            'reservation_number': '12345',
            'guest_name': 'John Doe',
            'start_date': '2024-01-01',
            'end_date': '2024-01-03',
            'room_name': 'Deluxe Room'
        }

        with patch.object(EmailService, "send_email", return_value={"status": "success"}) as send_mock:
            result = email_service.send_reservation_revision_notification(
                "guest@example.com",
                reservation_data
            )

        assert result["status"] == "success"
        send_mock.assert_called_once()


class TestLegacyFunction:
    """Test the legacy send_reservation_email function."""

    @patch('email_handler.current_app')
    @patch('email_handler.EmailService')
    @patch('email_handler.get_encryption_key', return_value="fake-key")
    @patch('email_handler.SessionLocal')
    def test_legacy_function_success(self, mock_session_local, _mock_get_key, mock_email_service_class, mock_current_app):
        """Test successful legacy function call."""
        # Mock the current_app.extensions
        mock_current_app.extensions = {'mail': Mock()}

        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = _build_email_config(
            user_id=1,
            is_active=True
        )
        mock_session_local.return_value = mock_session

        # Mock the EmailService instance
        mock_email_service = Mock()
        mock_email_service.send_reservation_confirmation.return_value = {
            "status": "success",
            "message": "Email sent successfully"
        }
        mock_email_service_class.return_value = mock_email_service

        result = send_reservation_email("test@example.com", "Reservation #12345 details", user_id=1)

        assert result["status"] == "success"
        mock_email_service.send_reservation_confirmation.assert_called_once()
        mock_session.close.assert_called_once()

    @patch('email_handler.current_app')
    def test_legacy_function_error(self, mock_current_app):
        """Test legacy function requires user_id for config lookup."""
        mock_current_app.extensions = {'mail': Mock()}

        result = send_reservation_email("test@example.com", "Reservation details")

        assert result["status"] == "error"
        assert "User ID is required" in result["message"]


class TestEmailTemplates:
    """Test email template generation."""

    @pytest.fixture
    def email_service(self):
        """Create EmailService instance for template testing."""
        return EmailService(_build_email_config())

    def test_reservation_confirmation_text_template(self, email_service):
        """Test reservation confirmation text template."""
        reservation_data = {
            'reservation_number': '12345',
            'guest_name': 'John Doe',
            'start_date': '2024-01-01',
            'end_date': '2024-01-03',
            'room_name': 'Deluxe Room'
        }

        text = email_service._create_reservation_confirmation_text(reservation_data)

        assert 'Reservation Number: 12345' in text
        assert 'John Doe' in text
        assert '2024-01-01' in text
        assert '2024-01-03' in text
        assert 'Deluxe Room' in text

    def test_reservation_confirmation_html_template(self, email_service):
        """Test reservation confirmation HTML template."""
        reservation_data = {
            'reservation_number': '12345',
            'guest_name': 'John Doe',
            'start_date': '2024-01-01',
            'end_date': '2024-01-03',
            'room_name': 'Deluxe Room'
        }

        html = email_service._create_reservation_confirmation_html(reservation_data)

        assert '<!DOCTYPE html>' in html
        assert 'Reservation Confirmation' in html
        assert 'Reservation Number' in html
        assert '12345' in html
        assert 'John Doe' in html
        assert '2024-01-01' in html
        assert '2024-01-03' in html
        assert 'Deluxe Room' in html

    def test_admin_checkin_notification_text_template(self, email_service):
        """Test admin check-in notification text template."""
        checkin_data = {
            'reservation_number': '12345',
            'guest_name': 'John Doe',
            'start_date': '2024-01-01',
            'end_date': '2024-01-03',
            'room_name': 'Deluxe Room',
            'client_name': 'John',
            'client_surname': 'Doe',
            'client_email': 'john@example.com',
            'client_phone': '+1234567890',
            'document_type': 'Passport',
            'document_number': 'AB123456',
            'has_front_image': True,
            'has_back_image': True,
            'has_selfie': True
        }

        text = email_service._create_admin_checkin_notification_text(checkin_data)

        assert 'Check-in Completed' in text
        assert 'Reservation Number: 12345' in text
        assert 'John Doe' in text
        assert 'john@example.com' in text
        assert 'Passport' in text
        assert 'AB123456' in text

    def test_admin_checkin_notification_html_template(self, email_service):
        """Test admin check-in notification HTML template."""
        checkin_data = {
            'reservation_number': '12345',
            'guest_name': 'John Doe',
            'start_date': '2024-01-01',
            'end_date': '2024-01-03',
            'room_name': 'Deluxe Room',
            'client_name': 'John',
            'client_surname': 'Doe',
            'client_email': 'john@example.com',
            'client_phone': '+1234567890',
            'document_type': 'Passport',
            'document_number': 'AB123456',
            'has_front_image': True,
            'has_back_image': True,
            'has_selfie': True
        }

        html = email_service._create_admin_checkin_notification_html(checkin_data)

        assert '<!DOCTYPE html>' in html
        assert 'Check-in Completed' in html
        assert 'Reservation Number' in html
        assert '12345' in html
        assert 'John Doe' in html
        assert 'john@example.com' in html
        assert 'Passport' in html
        assert 'AB123456' in html

    def test_reservation_approval_text_template(self, email_service):
        """Test reservation approval text template."""
        reservation_data = {
            'reservation_number': '12345',
            'guest_name': 'John Doe',
            'start_date': '2024-01-01',
            'end_date': '2024-01-03',
            'room_name': 'Deluxe Room'
        }

        text = email_service._create_reservation_approval_text(reservation_data)

        assert 'approved' in text.lower()
        assert 'Reservation Number: 12345' in text
        assert 'John Doe' in text
        assert '2024-01-01' in text
        assert '2024-01-03' in text
        assert 'Deluxe Room' in text

    def test_reservation_approval_html_template(self, email_service):
        """Test reservation approval HTML template."""
        reservation_data = {
            'reservation_number': '12345',
            'guest_name': 'John Doe',
            'start_date': '2024-01-01',
            'end_date': '2024-01-03',
            'room_name': 'Deluxe Room'
        }

        html = email_service._create_reservation_approval_html(reservation_data)

        assert '<!DOCTYPE html>' in html
        assert 'Reservation Approved' in html
        assert 'Reservation Number' in html
        assert '12345' in html
        assert 'John Doe' in html
        assert '2024-01-01' in html
        assert '2024-01-03' in html
        assert 'Deluxe Room' in html

    def test_reservation_revision_text_template(self, email_service):
        """Test reservation revision text template."""
        reservation_data = {
            'reservation_number': '12345',
            'guest_name': 'John Doe',
            'start_date': '2024-01-01',
            'end_date': '2024-01-03',
            'room_name': 'Deluxe Room'
        }

        text = email_service._create_reservation_revision_text(reservation_data)

        assert 'revision' in text.lower()
        assert 'Reservation Number: 12345' in text
        assert 'John Doe' in text
        assert '2024-01-01' in text
        assert '2024-01-03' in text
        assert 'Deluxe Room' in text

    def test_reservation_revision_html_template(self, email_service):
        """Test reservation revision HTML template."""
        reservation_data = {
            'reservation_number': '12345',
            'guest_name': 'John Doe',
            'start_date': '2024-01-01',
            'end_date': '2024-01-03',
            'room_name': 'Deluxe Room'
        }

        html = email_service._create_reservation_revision_html(reservation_data)

        assert '<!DOCTYPE html>' in html
        assert 'Reservation Requires Revision' in html
        assert 'Reservation Number' in html
        assert '12345' in html
        assert 'John Doe' in html
        assert '2024-01-01' in html
        assert '2024-01-03' in html
        assert 'Deluxe Room' in html


if __name__ == "__main__":
    pytest.main([__file__])
