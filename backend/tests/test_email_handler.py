"""
Tests for the email handler module.

This module tests the EmailService class and related functionality.
"""
#pylint: disable=C0301,E0611,E0401,W0718,R0914,E0401,C0411,W0212
from unittest.mock import Mock, patch
import pytest
from flask_mail import Mail
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


class TestEmailService:
    """Test the EmailService class."""

    @pytest.fixture
    def mock_mail(self):
        """Create a mock Flask-Mail instance."""
        return Mock(spec=Mail)

    @pytest.fixture
    def mock_app_config(self):
        """
        Return a minimal mock Flask-Mail configuration used by tests.
        
        The dictionary includes the keys required by EmailService initialization:
        - MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER
        
        Returns:
            dict: Mock Flask app config suitable for initializing Flask-Mail in tests.
        """
        return {
            'MAIL_SERVER': 'smtp.example.com',
            'MAIL_PORT': 587,
            'MAIL_USERNAME': 'test@example.com',
            'MAIL_PASSWORD': 'test_password',
            'MAIL_DEFAULT_SENDER': ('Test Sender', 'test@example.com')
        }

    @patch('email_handler.current_app')
    def test_email_service_initialization_success(self, mock_current_app, mock_mail, mock_app_config):
        """Test successful EmailService initialization."""
        mock_current_app.config = mock_app_config

        email_service = EmailService(mock_mail)
        assert email_service.mail == mock_mail

    @patch('email_handler.current_app')
    def test_email_service_initialization_missing_config(self, mock_current_app, mock_mail):
        """Test EmailService initialization with missing config."""
        mock_current_app.config = {}

        with pytest.raises(EmailServiceError, match="Missing required email configuration"):
            EmailService(mock_mail)

    @patch('email_handler.current_app')
    def test_validate_email_address_valid(self, mock_current_app, mock_mail, mock_app_config):
        """Test email address validation with valid email."""
        mock_current_app.config = mock_app_config

        email_service = EmailService(mock_mail)
        result = email_service.validate_email_address("test@example.com")
        assert result == "test@example.com"

    @patch('email_handler.current_app')
    def test_validate_email_address_invalid(self, mock_current_app, mock_mail, mock_app_config):
        """Test email address validation with invalid email."""
        mock_current_app.config = mock_app_config

        email_service = EmailService(mock_mail)

        with pytest.raises(EmailValidationError):
            email_service.validate_email_address("invalid-email")

    @patch('email_handler.current_app')
    def test_validate_email_list_valid(self, mock_current_app, mock_mail, mock_app_config):
        """Test email list validation with valid emails."""
        mock_current_app.config = mock_app_config

        email_service = EmailService(mock_mail)
        emails = ["test1@example.com", "test2@example.com"]
        result = email_service.validate_email_list(emails)
        assert result == emails

    @patch('email_handler.current_app')
    def test_validate_email_list_invalid(self, mock_current_app, mock_mail, mock_app_config):
        """Test email list validation with invalid emails."""
        mock_current_app.config = mock_app_config

        email_service = EmailService(mock_mail)
        emails = ["test1@example.com", "invalid-email"]

        with pytest.raises(EmailValidationError, match="Invalid email addresses"):
            email_service.validate_email_list(emails)

    @patch('email_handler.current_app')
    def test_send_email_success(self, mock_current_app, mock_mail, mock_app_config):
        """Test successful email sending."""
        mock_current_app.config = mock_app_config

        email_service = EmailService(mock_mail)

        email_data = EmailData(
            to_email="test@example.com",
            subject="Test Subject",
            body="Test Body"
        )

        result = email_service.send_email(email_data)

        assert result["status"] == "success"
        assert result["message"] == "Email sent successfully"
        assert result["to"] == "test@example.com"
        assert result["subject"] == "Test Subject"

        # Verify mail.send was called
        mock_mail.send.assert_called_once()

    @patch('email_handler.current_app')
    def test_send_email_validation_error(self, mock_current_app, mock_mail, mock_app_config):
        """Test email sending with validation error."""
        mock_current_app.config = mock_app_config

        email_service = EmailService(mock_mail)

        email_data = EmailData(
            to_email="invalid-email",
            subject="Test Subject",
            body="Test Body"
        )

        result = email_service.send_email(email_data)

        assert result["status"] == "error"
        assert "validation_error" in result["error_type"]

    @patch('email_handler.current_app')
    def test_send_reservation_confirmation(self, mock_current_app, mock_mail, mock_app_config):
        """Test sending reservation confirmation email."""
        mock_current_app.config = mock_app_config

        email_service = EmailService(mock_mail)

        reservation_data = {
            'reservation_number': '12345',
            'guest_name': 'John Doe',
            'start_date': '2024-01-01',
            'end_date': '2024-01-03',
            'room_name': 'Deluxe Room'
        }

        result = email_service.send_reservation_confirmation(
            "guest@example.com",
            reservation_data
        )

        assert result["status"] == "success"
        mock_mail.send.assert_called_once()

    @patch('email_handler.current_app')
    def test_send_reservation_update(self, mock_current_app, mock_mail, mock_app_config):
        """Test sending reservation update email."""
        mock_current_app.config = mock_app_config

        email_service = EmailService(mock_mail)

        reservation_data = {
            'reservation_number': '12345',
            'guest_name': 'John Doe',
            'start_date': '2024-01-01',
            'end_date': '2024-01-05',
            'room_name': 'Suite'
        }

        result = email_service.send_reservation_update(
            "guest@example.com",
            reservation_data
        )

        assert result["status"] == "success"
        mock_mail.send.assert_called_once()

    @patch('email_handler.current_app')
    def test_send_reservation_cancellation(self, mock_current_app, mock_mail, mock_app_config):
        """Test sending reservation cancellation email."""
        mock_current_app.config = mock_app_config

        email_service = EmailService(mock_mail)

        reservation_data = {
            'reservation_number': '12345',
            'guest_name': 'John Doe',
            'start_date': '2024-01-01',
            'end_date': '2024-01-03',
            'room_name': 'Deluxe Room'
        }

        result = email_service.send_reservation_cancellation(
            "guest@example.com",
            reservation_data
        )

        assert result["status"] == "success"
        mock_mail.send.assert_called_once()

    @patch('email_handler.current_app')
    def test_send_admin_checkin_notification(self, mock_current_app, mock_mail, mock_app_config):
        """Test sending admin check-in notification email."""
        mock_current_app.config = mock_app_config

        email_service = EmailService(mock_mail)

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

        result = email_service.send_admin_checkin_notification(
            "admin@example.com",
            checkin_data
        )

        assert result["status"] == "success"
        mock_mail.send.assert_called_once()

    @patch('email_handler.current_app')
    def test_send_reservation_approval_notification(self, mock_current_app, mock_mail, mock_app_config):
        """Test sending reservation approval notification email."""
        mock_current_app.config = mock_app_config

        email_service = EmailService(mock_mail)

        reservation_data = {
            'reservation_number': '12345',
            'guest_name': 'John Doe',
            'start_date': '2024-01-01',
            'end_date': '2024-01-03',
            'room_name': 'Deluxe Room'
        }

        result = email_service.send_reservation_approval_notification(
            "guest@example.com",
            reservation_data
        )

        assert result["status"] == "success"
        mock_mail.send.assert_called_once()

    @patch('email_handler.current_app')
    def test_send_reservation_revision_notification(self, mock_current_app, mock_mail, mock_app_config):
        """Test sending reservation revision notification email."""
        mock_current_app.config = mock_app_config

        email_service = EmailService(mock_mail)

        reservation_data = {
            'reservation_number': '12345',
            'guest_name': 'John Doe',
            'start_date': '2024-01-01',
            'end_date': '2024-01-03',
            'room_name': 'Deluxe Room'
        }

        result = email_service.send_reservation_revision_notification(
            "guest@example.com",
            reservation_data
        )

        assert result["status"] == "success"
        mock_mail.send.assert_called_once()


class TestLegacyFunction:
    """Test the legacy send_reservation_email function."""

    @patch('email_handler.current_app')
    @patch('email_handler.EmailService')
    def test_legacy_function_success(self, mock_email_service_class, mock_current_app):
        """Test successful legacy function call."""
        # Mock the current_app.extensions
        mock_current_app.extensions = {'mail': Mock()}

        # Mock the EmailService instance
        mock_email_service = Mock()
        mock_email_service.send_reservation_confirmation.return_value = {
            "status": "success",
            "message": "Email sent successfully"
        }
        mock_email_service_class.return_value = mock_email_service

        result = send_reservation_email("test@example.com", "Reservation #12345 details")

        assert result["status"] == "success"
        mock_email_service.send_reservation_confirmation.assert_called_once()

    @patch('email_handler.current_app')
    def test_legacy_function_error(self, mock_current_app):
        """Test legacy function with error."""
        mock_current_app.extensions = {'mail': Mock()}

        # Force an error by making current_app.extensions['mail'] raise an exception
        mock_current_app.extensions['mail'].side_effect = Exception("Test error")

        result = send_reservation_email("test@example.com", "Reservation details")

        assert result["status"] == "error"
        assert "Test error" in result["message"]


class TestEmailTemplates:
    """Test email template generation."""

    @pytest.fixture
    def email_service(self):
        """Create EmailService instance for template testing."""
        mock_mail = Mock(spec=Mail)
        mock_app_config = {
            'MAIL_SERVER': 'smtp.example.com',
            'MAIL_PORT': 587,
            'MAIL_USERNAME': 'test@example.com',
            'MAIL_PASSWORD': 'test_password',
            'MAIL_DEFAULT_SENDER': ('Test Sender', 'test@example.com')
        }

        with patch('email_handler.current_app') as mock_current_app:
            mock_current_app.config = mock_app_config
            return EmailService(mock_mail)

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

        assert 'Reservation #12345' in text
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
        assert 'Reservation Confirmed!' in html
        assert 'Reservation #12345' in html
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
        assert 'Reservation #12345' in text
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
        assert 'Reservation #12345' in html
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

        assert 'Reservation Approved' in text
        assert 'Reservation #12345' in text
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
        assert 'Reservation #12345' in html
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

        assert 'Reservation Requires Revision' in text
        assert 'Reservation #12345' in text
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
        assert 'Reservation #12345' in html
        assert 'John Doe' in html
        assert '2024-01-01' in html
        assert '2024-01-03' in html
        assert 'Deluxe Room' in html


if __name__ == "__main__":
    pytest.main([__file__])
