# pylint: disable=C0301,E0611,E0401,W0718,R0914,C0302,W0107,C0303
"""
Email handling module for the remote check-in system.

This module provides a comprehensive email service for sending various types of emails
including reservation confirmations, updates, and cancellations.
"""

import logging
import json
import re
import smtplib
import traceback
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from email_validator import validate_email, EmailNotValidError
from flask import current_app
from cryptography.fernet import Fernet
import requests
from utils.encryption_utils import get_encryption_key
from models import EmailConfig
from database import SessionLocal

logger = logging.getLogger(__name__)

@dataclass
class EmailData:
    """Data class for email information."""
    to_email: str
    subject: str
    body: str
    html_body: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None


class EmailValidationError(Exception):
    """Custom exception for email validation errors."""
    pass


class EmailServiceError(Exception):
    """Custom exception for email service errors."""
    pass


class EmailService:
    """
    Comprehensive email service for handling all email operations.

    This service provides methods for sending various types of emails,
    validating email addresses, and managing email templates.
    Supports both SMTP and external providers like Mailgun, SendGrid.
    """

    def __init__(self, config: 'EmailConfig', encryption_key: str = None):
        """
        Initialize the EmailService.
        
        Initializes internal state from an EmailConfig (required) and prepares provider-specific settings.
        An optional Fernet encryption key may be provided to decrypt stored provider credentials; if omitted
        the service will attempt to obtain a key from application configuration or use credentials as-is.
        
        Parameters:
            encryption_key (str, optional): Fernet key used to decrypt encrypted provider passwords.
        
        Raises:
            EmailServiceError: If no EmailConfig is provided.
        """
        if not config:
            raise EmailServiceError("EmailConfig is required")

        self.config = config
        self.encryption_key = encryption_key
        self.provider_type = config.provider_type or 'smtp'
        self.provider_config = json.loads(config.provider_config) if config.provider_config else {}

        self._setup_from_config()

    def _setup_from_config(self) -> None:
        """
        Initialize internal state from the provided EmailConfig.
        
        Reads required values from self.config, decrypts the stored mail password and sets
        self.decrypted_password for use by sending methods. Raises EmailServiceError if
        no configuration is present.
        """
        if not self.config:
            raise EmailServiceError("No configuration provided")

        # Store the decrypted password for use in sending emails
        self.decrypted_password = self._decrypt_password(self.config.mail_password)

        # We don't need to create a Flask app - we'll use the existing one
        # and override the mail configuration when sending emails

    def _decrypt_password(self, encrypted_password: str) -> str:
        """
        Decrypts an encrypted password string and returns the plaintext.
        
        If encrypted_password is falsy (None or empty) returns an empty string. The method attempts to use the instance's encryption_key, falling back to the Flask app config key 'ENCRYPTION_KEY' when available. If no key is found, the function treats the provided value as already plaintext and returns it unchanged (backward compatibility). On decryption errors the underlying exception is re-raised.
        """
        if not encrypted_password:
            logger.warning("Encrypted password is empty or None")
            return ""

        try:
            # Use encryption key passed to constructor, or try to get from current app context
            key = self.encryption_key
            if not key:
                try:
                    key = current_app.config.get('ENCRYPTION_KEY')
                except RuntimeError:
                    # current_app is not available in this context
                    logger.warning("No Flask app context available for decryption")

            if not key:
                # If no encryption key, assume password is not encrypted (for backward compatibility)
                logger.info("No encryption key found, using password as-is")
                return encrypted_password

            # Ensure key is bytes
            if isinstance(key, str):
                key = key.encode()

            f = Fernet(key)
            return f.decrypt(encrypted_password.encode()).decode()
        except Exception as e:
            logger.error("Failed to decrypt password: %s", str(e))
            logger.error("Encrypted password type: %s, length: %s",
                        type(encrypted_password), len(encrypted_password) if encrypted_password else 'None')
            logger.error("Key type: %s", type(key) if 'key' in locals() else 'None')
            raise e

    def validate_email_address(self, email: str) -> str:
        """
        Validate and normalize an email address using strict syntax rules.
        
        Performs syntactic validation via the `email_validator` library (deliverability is not checked)
        and returns the normalized form (e.g., lowercasing and canonicalization).
        
        Parameters:
            email (str): The email address to validate.
        
        Returns:
            str: The normalized email address.
        
        Raises:
            EmailValidationError: If the address is syntactically invalid.
        """
        try:
            # Validate and normalize email
            validated_email = validate_email(email, check_deliverability=False)
            return validated_email.normalized
        except EmailNotValidError as e:
            raise EmailValidationError(f"Invalid email address: {str(e)}") from e

    def validate_email_address_lenient(self, email: str) -> str:
        """
        Leniently validate and normalize an email address.
        
        Performs basic checks (presence of '@' and a dot in the domain part), trims surrounding whitespace,
        and lowercases the result. Intended as a non-strict fallback when strict validation is not required.
        
        Parameters:
            email (str): The email address to validate and normalize.
        
        Returns:
            str: The normalized email address (trimmed and lowercased).
        
        Raises:
            EmailValidationError: If `email` is missing, not a string, or fails the basic format check.
        """
        if not email or not isinstance(email, str):
            raise EmailValidationError("Email address is required")

        # Basic email format check
        email = email.strip().lower()
        if '@' not in email or '.' not in email.split('@')[-1]:
            raise EmailValidationError("Invalid email format")

        # Remove any whitespace and normalize
        email = email.strip()

        return email

    def validate_email_list(self, emails: List[str]) -> List[str]:
        """
        Validate and normalize a list of email addresses.
        
        Each address is validated using the service's strict validator (validate_email_address).
        Returns the list of normalized addresses in the same order. If any address fails
        validation, raises EmailValidationError listing the invalid entries.
        """
        validated_emails = []
        invalid_emails = []

        for email in emails:
            try:
                validated_email = self.validate_email_address(email)
                validated_emails.append(validated_email)
            except EmailValidationError:
                invalid_emails.append(email)

        if invalid_emails:
            raise EmailValidationError(
                f"Invalid email addresses: {', '.join(invalid_emails)}"
            )

        return validated_emails

    def send_email(self, email_data: EmailData) -> Dict[str, Any]:
        """
        Send an email using the configured provider (SMTP, Mailgun, or SendGrid).
        
        Routes the provided EmailData to the provider configured for this EmailService instance and returns a structured result describing success or failure. On validation errors or send failures the result contains "status": "error", a human-readable "message", and an "error_type" (e.g., "validation_error" or "send_error").
        
        Parameters:
            email_data (EmailData): Email payload (recipient, subject, plain text body; may include html_body, attachments, cc, bcc).
        
        Returns:
            Dict[str, Any]: Result dictionary with at least "status" ("success" or "error") and "message"; may include provider-specific details or an "error_type" on failure.
        """
        try:
            logger.info("Preparing to send email to: %s using %s", email_data.to_email, self.provider_type)

            # Route to appropriate provider
            if self.provider_type == 'mailgun':
                return self._send_via_mailgun(email_data)
            if self.provider_type == 'sendgrid':
                return self._send_via_sendgrid(email_data)
            # Default to SMTP
            return self._send_via_smtp(email_data)

        except EmailValidationError as e:
            logger.error("Email validation error: %s", str(e))
            return {
                "status": "error",
                "message": f"Email validation failed: {str(e)}",
                "error_type": "validation_error"
            }
        except Exception as e:
            logger.error("Failed to send email to %s: %s", email_data.to_email, str(e))
            return {
                "status": "error",
                "message": f"Failed to send email: {str(e)}",
                "error_type": "send_error"
            }

    def _send_via_smtp(self, email_data: EmailData) -> Dict[str, Any]:
        """
        Send an email via SMTP using the configured server.
        
        This method builds a multipart MIME message from the provided EmailData (plain text and/or HTML bodies, optional attachments, optional CC/BCC), connects to the configured SMTP server (with optional SSL/TLS), authenticates using the decrypted credentials stored on the service, and sends the message to all recipients.
        
        Returns:
            dict: A success result containing keys "status", "message", "to", "subject", and "provider" on successful send.
        
        Raises:
            EmailServiceError: If any error occurs while constructing the message, connecting, authenticating, or sending.
        """

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = email_data.subject
            # Format sender name as "Remote Check-in System ('B&B Chapeau')"
            sender_name = self.config.mail_default_sender_name if self.config.mail_default_sender_name and self.config.mail_default_sender_name.strip() else 'Remote Check-in'
            formatted_sender_name = f"Remote Check-in System ('{sender_name}')"

            msg['From'] = formataddr((formatted_sender_name, self.config.mail_default_sender_email))
            msg['To'] = email_data.to_email

            # Add CC and BCC if provided
            if email_data.cc:
                msg['Cc'] = ', '.join(email_data.cc)
            if email_data.bcc:
                msg['Bcc'] = ', '.join(email_data.bcc)

            # Add body parts
            if email_data.body:
                text_part = MIMEText(email_data.body, 'plain', 'utf-8')
                msg.attach(text_part)

            if email_data.html_body:
                html_part = MIMEText(email_data.html_body, 'html', 'utf-8')
                msg.attach(html_part)

            # Add attachments if provided
            if email_data.attachments:
                for attachment in email_data.attachments:

                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['data'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment["filename"]}'
                    )
                    msg.attach(part)

            # Prepare recipients list before connecting
            recipients = [email_data.to_email]
            if email_data.cc:
                recipients.extend(email_data.cc)
            if email_data.bcc:
                recipients.extend(email_data.bcc)

            # Connect to SMTP server using context manager with timeout
            timeout = getattr(self.config, 'mail_timeout', 30)  # Default 30 seconds if not configured

            if self.config.mail_use_ssl:
                with smtplib.SMTP_SSL(self.config.mail_server, self.config.mail_port, timeout=timeout) as server:
                    server.login(self.config.mail_username, self.decrypted_password)
                    server.send_message(msg, to_addrs=recipients)
            else:
                with smtplib.SMTP(self.config.mail_server, self.config.mail_port, timeout=timeout) as server:
                    if self.config.mail_use_tls:
                        server.starttls()
                    server.login(self.config.mail_username, self.decrypted_password)
                    server.send_message(msg, to_addrs=recipients)

            logger.info("Email sent successfully via SMTP to: %s", email_data.to_email)
            return {
                "status": "success",
                "message": "Email sent successfully",
                "to": email_data.to_email,
                "subject": email_data.subject,
                "provider": "smtp"
            }

        except Exception as e:
            logger.error("SMTP error: %s", str(e))
            raise EmailServiceError(f"Failed to send email via SMTP: {str(e)}") from e

    def _send_via_mailgun(self, email_data: EmailData) -> Dict[str, Any]:
        """
        Send the given EmailData using the Mailgun HTTP API.
        
        Uses provider_config['domain'] and provider_config['api_key'] from the service configuration. The EmailData fields used are: to_email, subject, body (text) and html_body (optional). The sender address and display name are derived from the service config.
        
        Returns:
            dict: On success, returns a dictionary with keys: "status", "message", "to", "subject", "provider", and "response" (Mailgun JSON response).
        
        Raises:
            EmailServiceError: If Mailgun domain or API key are missing, or if the Mailgun API returns a non-200 response.
        """
        domain = self.provider_config.get('domain')
        api_key = self.provider_config.get('api_key')

        if not domain or not api_key:
            raise EmailServiceError("Mailgun domain and API key are required")

        url = f"https://api.mailgun.net/v3/{domain}/messages"

        sender_name = self.config.mail_default_sender_name if self.config.mail_default_sender_name and self.config.mail_default_sender_name.strip() else "Remote Check-in"
        formatted_sender_name = f"Remote Check-in System ('{sender_name}')"
        data = {
            "from": f"{formatted_sender_name} <{self.config.mail_default_sender_email}>",
            "to": email_data.to_email,
            "subject": email_data.subject,
            "text": email_data.body,
            "html": email_data.html_body
        }

        response = requests.post(
            url,
            auth=("api", api_key),
            data=data,
            timeout=30
        )

        if response.status_code == 200:
            logger.info("Email sent successfully via Mailgun to: %s", email_data.to_email)
            return {
                "status": "success",
                "message": "Email sent successfully via Mailgun",
                "to": email_data.to_email,
                "subject": email_data.subject,
                "provider": "mailgun",
                "response": response.json()
            }
        raise EmailServiceError(f"Mailgun API error: {response.status_code} - {response.text}")

    def _send_via_sendgrid(self, email_data: EmailData) -> Dict[str, Any]:
        """
        Send the given EmailData using the SendGrid Web API.
        
        This builds a SendGrid JSON payload using email_data.to_email, subject, plain-text body, and optional HTML body, and sends it from the configured default sender in self.config. Requires a SendGrid API key in self.provider_config['api_key'].
        
        Returns:
            dict: A status dictionary on success containing keys like "status", "message", "to", "subject", and "provider".
        
        Raises:
            EmailServiceError: If the SendGrid API key is missing or the API responds with a non-202 error.
        """
        api_key = self.provider_config.get('api_key')

        if not api_key:
            raise EmailServiceError("SendGrid API key is required")

        url = "https://api.sendgrid.com/v3/mail/send"

        payload = {
            "personalizations": [
                {
                    "to": [{"email": email_data.to_email}],
                    "subject": email_data.subject
                }
            ],
            "from": {
                "email": self.config.mail_default_sender_email,
                "name": f"Remote Check-in System ('{self.config.mail_default_sender_name if self.config.mail_default_sender_name and self.config.mail_default_sender_name.strip() else 'Remote Check-in'}')"  # pylint: disable=line-too-long
            },
            "content": [
                {
                    "type": "text/plain",
                    "value": email_data.body
                },
                {
                    "type": "text/html",
                    "value": email_data.html_body
                }
            ]
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)

        if response.status_code == 202:
            logger.info("Email sent successfully via SendGrid to: %s", email_data.to_email)
            return {
                "status": "success",
                "message": "Email sent successfully via SendGrid",
                "to": email_data.to_email,
                "subject": email_data.subject,
                "provider": "sendgrid"
            }
        raise EmailServiceError(f"SendGrid API error: {response.status_code} - {response.text}")

    def send_reservation_confirmation(
        self,
        client_email: str,
        reservation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send a reservation confirmation email to a client.
        
        Attempts strict validation of client_email and falls back to lenient validation; if both fail returns an error dict with "status": "error" and "error_type": "validation_error". On success, builds plain-text and HTML confirmation bodies from reservation_data, constructs an EmailData payload, and delegates sending to self.send_email.
        
        Args:
            client_email (str): Recipient email address to validate and use as the target.
            reservation_data (Dict[str, Any]): Reservation fields used to populate templates (e.g., reservation_number, guest_name, start_date, end_date, room_name).
        
        Returns:
            Dict[str, Any]: Result from send_email on success, or an error dictionary containing "status", "message", and "error_type" (possible values include "validation_error" and "creation_error").
        """
        try:
            # Validate client email first
            try:
                validated_email = self.validate_email_address(client_email)
                logger.info("Email validation successful: %s -> %s", client_email, validated_email)
            except EmailValidationError as e:
                logger.warning("Strict email validation failed for %s: %s", client_email, str(e))
                # Try lenient validation as fallback
                try:
                    validated_email = self.validate_email_address_lenient(client_email)
                    logger.info("Lenient email validation successful: %s -> %s", client_email, validated_email)
                except EmailValidationError as e2:
                    logger.error("Both strict and lenient email validation failed for %s: %s", client_email, str(e2))
                    return {
                        "status": "error",
                        "message": f"Invalid email address: {str(e2)}",
                        "error_type": "validation_error"
                    }

            # Create email content
            subject = f"Reservation Confirmation - {reservation_data.get('reservation_number', 'N/A')}"

            # Plain text body
            body = self._create_reservation_confirmation_text(reservation_data)

            # HTML body
            html_body = self._create_reservation_confirmation_html(reservation_data)

            # Create email data
            email_data = EmailData(
                to_email=validated_email,  # Use validated email
                subject=subject,
                body=body,
                html_body=html_body
            )

            logger.info("Sending reservation confirmation to: %s", validated_email)
            return self.send_email(email_data)

        except Exception as e:
            logger.error("Error creating reservation confirmation email: %s", str(e))
            logger.error("Traceback: %s", traceback.format_exc())
            return {
                "status": "error",
                "message": f"Error creating email: {str(e)}",
                "error_type": "creation_error"
            }

    def send_reservation_update(
        self,
        client_email: str,
        reservation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send a reservation update email to a client.
        
        Constructs plain-text and HTML bodies from reservation_data, wraps them in an EmailData object, and sends via the configured provider.
        
        Parameters:
            client_email (str): Recipient email address (validated by send_email).
            reservation_data (Dict[str, Any]): Reservation fields used to build the message (e.g., reservation_number, guest_name, dates, room_name).
        
        Returns:
            Dict[str, Any]: Result dictionary from send_email on success, or an error dictionary with keys "status", "message", and "error_type" on failure.
        """
        try:
            subject = f"Reservation Update - {reservation_data.get('reservation_number', 'N/A')}"

            body = self._create_reservation_update_text(reservation_data)
            html_body = self._create_reservation_update_html(reservation_data)

            email_data = EmailData(
                to_email=client_email,
                subject=subject,
                body=body,
                html_body=html_body
            )

            return self.send_email(email_data)

        except Exception as e:
            logger.error("Error creating reservation update email: %s", str(e))
            return {
                "status": "error",
                "message": f"Error creating email: {str(e)}",
                "error_type": "creation_error"
            }

    def send_reservation_cancellation(
        self,
        client_email: str,
        reservation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send a reservation cancellation email to the specified client.
        
        Builds plain-text and HTML cancellation content from reservation_data, constructs an EmailData payload, and delegates delivery to send_email. If message creation fails an error dictionary is returned.
        
        Parameters:
            client_email (str): Recipient email address.
            reservation_data (Dict[str, Any]): Reservation fields used to render templates (e.g., reservation_number, guest_name, start_date, end_date, room_name).
        
        Returns:
            Dict[str, Any]: Result from send_email on success, or an error dictionary with keys "status", "message", and "error_type" if email creation fails.
        """
        try:
            subject = f"Reservation Cancellation - {reservation_data.get('reservation_number', 'N/A')}"

            body = self._create_reservation_cancellation_text(reservation_data)
            html_body = self._create_reservation_cancellation_html(reservation_data)

            email_data = EmailData(
                to_email=client_email,
                subject=subject,
                body=body,
                html_body=html_body
            )

            return self.send_email(email_data)

        except Exception as e:
            logger.error("Error creating reservation cancellation email: %s", str(e))
            return {
                "status": "error",
                "message": f"Error creating email: {str(e)}",
                "error_type": "creation_error"
            }

    def _create_reservation_confirmation_text(self, reservation_data: Dict[str, Any]) -> str:
        """Create plain text body for reservation confirmation."""
        # Safely get values and convert to strings
        reservation_number = str(reservation_data.get('reservation_number', 'N/A'))
        guest_name = str(reservation_data.get('guest_name', 'N/A'))
        start_date = str(reservation_data.get('start_date', 'N/A'))
        end_date = str(reservation_data.get('end_date', 'N/A'))
        room_name = str(reservation_data.get('room_name', 'N/A'))

        return f"""
Dear Guest,

Your reservation has been confirmed successfully!

Reservation Details:
- Reservation Number: {reservation_number}
- Guest Name: {guest_name}
- Check-in Date: {start_date}
- Check-out Date: {end_date}
- Room: {room_name}

We look forward to welcoming you!

Best regards,
The Remote Check-in Team
        """.strip()

    def _create_reservation_confirmation_html(self, reservation_data: Dict[str, Any]) -> str:
        """
        Return an HTML-formatted reservation confirmation email body.
        
        Generates a self-contained HTML document for a reservation confirmation using fields from
        the provided reservation_data. Values for the following keys are read and coerced to strings;
        missing keys are replaced with 'N/A':
        - reservation_number
        - guest_name
        - start_date
        - end_date
        - room_name
        
        Parameters:
            reservation_data (Dict[str, Any]): Mapping containing reservation fields listed above.
        
        Returns:
            str: Complete HTML document as a string suitable for use as an email HTML body.
        """
        # Safely get values and convert to strings
        reservation_number = str(reservation_data.get('reservation_number', 'N/A'))
        guest_name = str(reservation_data.get('guest_name', 'N/A'))
        start_date = str(reservation_data.get('start_date', 'N/A'))
        end_date = str(reservation_data.get('end_date', 'N/A'))
        room_name = str(reservation_data.get('room_name', 'N/A'))

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Reservation Confirmation</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .details {{ background-color: white; padding: 15px; margin: 20px 0; border-left: 4px solid #4CAF50; }}
        .footer {{ text-align: center; padding: 20px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Reservation Confirmed!</h1>
        </div>
        <div class="content">
            <p>Dear Guest,</p>
            <p>Your reservation has been confirmed successfully!</p>

            <div class="details">
                <h3>Reservation Details:</h3>
                <p><strong>Reservation Number:</strong> {reservation_number}</p>
                <p><strong>Guest Name:</strong> {guest_name}</p>
                <p><strong>Check-in Date:</strong> {start_date}</p>
                <p><strong>Check-out Date:</strong> {end_date}</p>
                <p><strong>Room:</strong> {room_name}</p>
            </div>

            <p>We look forward to welcoming you!</p>
        </div>
        <div class="footer">
            <p>Best regards,<br>The Remote Check-in Team</p>
        </div>
    </div>
</body>
</html>
        """.strip()

    def _create_reservation_update_text(self, reservation_data: Dict[str, Any]) -> str:
        """
        Return a plain-text email body notifying a guest that their reservation was updated.
        
        The function formats a short message using values from reservation_data. Expected keys (string values) and their defaults if missing:
        - reservation_number: reservation identifier (defaults to 'N/A')
        - guest_name: guest's full name (defaults to 'N/A')
        - start_date: check-in date (defaults to 'N/A')
        - end_date: check-out date (defaults to 'N/A')
        - room_name: name or type of the room (defaults to 'N/A')
        
        Returns:
            A formatted plain-text string suitable for the body of an update notification email.
        """
        return f"""
Dear Guest,

Your reservation has been updated successfully!

Updated Reservation Details:
- Reservation Number: {reservation_data.get('reservation_number', 'N/A')}
- Guest Name: {reservation_data.get('guest_name', 'N/A')}
- Check-in Date: {reservation_data.get('start_date', 'N/A')}
- Check-out Date: {reservation_data.get('end_date', 'N/A')}
- Room: {reservation_data.get('room_name', 'N/A')}

If you have any questions, please don't hesitate to contact us.

Best regards,
The Remote Check-in Team
        """.strip()

    def _create_reservation_update_html(self, reservation_data: Dict[str, Any]) -> str:
        """
        Return an HTML-formatted email body for a reservation update.
        
        Generates a complete HTML document (styled and ready to send as an HTML email) that summarizes the updated reservation details.
        
        Parameters:
            reservation_data (Dict[str, Any]): Mapping containing reservation fields used in the template. Expected keys (strings) include:
                - 'reservation_number': reservation identifier (displayed or 'N/A' if missing)
                - 'guest_name': guest's full name
                - 'start_date': check-in date
                - 'end_date': check-out date
                - 'room_name': assigned room name
        
        Returns:
            str: The rendered HTML string for the reservation update email.
        """
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Reservation Update</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2196F3; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .details {{ background-color: white; padding: 15px; margin: 20px 0; border-left: 4px solid #2196F3; }}
        .footer {{ text-align: center; padding: 20px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Reservation Updated</h1>
        </div>
        <div class="content">
            <p>Dear Guest,</p>
            <p>Your reservation has been updated successfully!</p>

            <div class="details">
                <h3>Updated Reservation Details:</h3>
                <p><strong>Reservation Number:</strong> {reservation_data.get('reservation_number', 'N/A')}</p>
                <p><strong>Guest Name:</strong> {reservation_data.get('guest_name', 'N/A')}</p>
                <p><strong>Check-in Date:</strong> {reservation_data.get('start_date', 'N/A')}</p>
                <p><strong>Check-out Date:</strong> {reservation_data.get('end_date', 'N/A')}</p>
                <p><strong>Room:</strong> {reservation_data.get('room_name', 'N/A')}</p>
            </div>

            <p>If you have any questions, please don't hesitate to contact us.</p>
        </div>
        <div class="footer">
            <p>Best regards,<br>The Remote Check-in Team</p>
        </div>
    </div>
</body>
</html>
        """.strip()

    def _create_reservation_cancellation_text(self, reservation_data: Dict[str, Any]) -> str:
        """
        Builds the plain-text email body for a reservation cancellation.
        
        reservation_data should be a dict containing reservation fields used to populate the template. Known keys:
        - reservation_number
        - guest_name
        - start_date
        - end_date
        - room_name
        
        Missing keys are replaced with 'N/A'.
        
        Returns:
            str: Formatted plain-text cancellation message.
        """
        return f"""
Dear Guest,

Your reservation has been cancelled.

Cancelled Reservation Details:
- Reservation Number: {reservation_data.get('reservation_number', 'N/A')}
- Guest Name: {reservation_data.get('guest_name', 'N/A')}
- Check-in Date: {reservation_data.get('start_date', 'N/A')}
- Check-out Date: {reservation_data.get('end_date', 'N/A')}
- Room: {reservation_data.get('room_name', 'N/A')}

If you have any questions or if this cancellation was made in error, please contact us immediately.

Best regards,
The Remote Check-in Team
        """.strip()

    def _create_reservation_cancellation_html(self, reservation_data: Dict[str, Any]) -> str:
        """
        Return an HTML-formatted email body for a reservation cancellation.
        
        Parameters:
            reservation_data (dict): Mapping with reservation fields used to populate the template.
                Expected keys (optional): 'reservation_number', 'guest_name', 'start_date',
                'end_date', 'room_name'. Missing keys will be rendered as 'N/A'.
        
        Returns:
            str: Complete HTML string for the cancellation email body (UTF-8, safe to embed
            in a multipart message as the HTML part).
        """
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Reservation Cancellation</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #f44336; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .details {{ background-color: white; padding: 15px; margin: 20px 0; border-left: 4px solid #f44336; }}
        .footer {{ text-align: center; padding: 20px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Reservation Cancelled</h1>
        </div>
        <div class="content">
            <p>Dear Guest,</p>
            <p>Your reservation has been cancelled.</p>

            <div class="details">
                <h3>Cancelled Reservation Details:</h3>
                <p><strong>Reservation Number:</strong> {reservation_data.get('reservation_number', 'N/A')}</p>
                <p><strong>Guest Name:</strong> {reservation_data.get('guest_name', 'N/A')}</p>
                <p><strong>Check-in Date:</strong> {reservation_data.get('start_date', 'N/A')}</p>
                <p><strong>Check-out Date:</strong> {reservation_data.get('end_date', 'N/A')}</p>
                <p><strong>Room:</strong> {reservation_data.get('room_name', 'N/A')}</p>
            </div>

            <p>If you have any questions or if this cancellation was made in error, please contact us immediately.</p>
        </div>
        <div class="footer">
            <p>Best regards,<br>The Remote Check-in Team</p>
        </div>
    </div>
</body>
</html>
        """.strip()

    def send_admin_checkin_notification(
        self,
        admin_email: str,
        checkin_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send check-in completion notification to admin.

        Args:
            admin_email: Admin's email address
            checkin_data: Dictionary containing check-in details

        Returns:
            Dictionary with status and message
        """
        try:
            # Validate admin email first
            try:
                validated_email = self.validate_email_address(admin_email)
                logger.info("Admin email validation successful: %s -> %s", admin_email, validated_email)
            except EmailValidationError as e:
                logger.warning("Strict email validation failed for admin %s: %s", admin_email, str(e))
                # Try lenient validation as fallback
                try:
                    validated_email = self.validate_email_address_lenient(admin_email)
                    logger.info("Lenient admin email validation successful: %s -> %s", admin_email, validated_email)
                except EmailValidationError as e2:
                    logger.error("Both strict and lenient email validation failed for admin %s: %s", admin_email, str(e2))
                    return {
                        "status": "error",
                        "message": f"Invalid admin email address: {str(e2)}",
                        "error_type": "validation_error"
                    }

            # Create email content
            subject = f"New Check-in Completed - {checkin_data.get('reservation_number', 'N/A')}"

            # Plain text body
            body = self._create_admin_checkin_notification_text(checkin_data)

            # HTML body
            html_body = self._create_admin_checkin_notification_html(checkin_data)

            # Create email data
            email_data = EmailData(
                to_email=validated_email,  # Use validated email
                subject=subject,
                body=body,
                html_body=html_body
            )

            logger.info("Sending admin check-in notification to: %s", validated_email)
            return self.send_email(email_data)

        except Exception as e:
            logger.error("Error creating admin check-in notification email: %s", str(e))
            logger.error("Traceback: %s", traceback.format_exc())
            return {
                "status": "error",
                "message": f"Error creating admin notification email: {str(e)}",
                "error_type": "creation_error"
            }

    def _create_admin_checkin_notification_text(self, checkin_data: Dict[str, Any]) -> str:
        """
        Builds the plain-text body for an admin notification email when a client completes check-in.
        
        Parameters:
            checkin_data (dict): Mapping containing reservation and client fields used to populate the message. Expected keys include:
                - reservation_number, guest_name, start_date, end_date, room_name
                - client_name, client_surname, client_email, client_phone
                - document_type, document_number
                - has_front_image, has_back_image, has_selfie
                Missing keys are rendered as 'N/A'; boolean document flags control uploaded/missing markers.
        
        Returns:
            str: Rendered plain-text email body.
        """
        return f"""
New Check-in Completed

A client has completed the check-in process for the following reservation:

Reservation Details:
- Reservation Number: {checkin_data.get('reservation_number', 'N/A')}
- Guest Name: {checkin_data.get('guest_name', 'N/A')}
- Check-in Date: {checkin_data.get('start_date', 'N/A')}
- Check-out Date: {checkin_data.get('end_date', 'N/A')}
- Room: {checkin_data.get('room_name', 'N/A')}

Client Information:
- Name: {checkin_data.get('client_name', 'N/A')}
- Surname: {checkin_data.get('client_surname', 'N/A')}
- Email: {checkin_data.get('client_email', 'N/A')}
- Phone: {checkin_data.get('client_phone', 'N/A')}
- Document Type: {checkin_data.get('document_type', 'N/A')}
- Document Number: {checkin_data.get('document_number', 'N/A')}

Uploaded Documents:
- Front Document: {'✓ Uploaded' if checkin_data.get('has_front_image') else '✗ Missing'}
- Back Document: {'✓ Uploaded' if checkin_data.get('has_back_image') else '✗ Missing'}
- Selfie: {'✓ Uploaded' if checkin_data.get('has_selfie') else '✗ Missing'}

Please review the uploaded documents and client information in the admin panel.

Best regards,
Remote Check-in System
        """.strip()

    def _create_admin_checkin_notification_html(self, checkin_data: Dict[str, Any]) -> str:
        """
        Builds an HTML-formatted admin notification for a completed check-in.
        
        Parameters:
            checkin_data (Dict[str, Any]): Mapping with reservation and client fields used to populate the template. Expected keys (all optional; missing values render as "N/A"):
                - reservation_number, guest_name, start_date, end_date, room_name
                - client_name, client_surname, client_email, client_phone
                - document_type, document_number
                - has_front_image, has_back_image, has_selfie (booleans indicating uploaded document status)
        
        Returns:
            str: Complete HTML document as a string suitable for use as an email body (includes inline styles and status indicators for uploaded/missing documents).
        """
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Check-in Completed</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 8px 8px 0 0;
        }}
        .content {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 0 0 8px 8px;
        }}
        .section {{
            margin-bottom: 20px;
            padding: 15px;
            background-color: white;
            border-radius: 5px;
            border-left: 4px solid #3498db;
        }}
        .section h3 {{
            margin-top: 0;
            color: #2c3e50;
        }}
        .info-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            padding: 5px 0;
            border-bottom: 1px solid #eee;
        }}
        .info-row:last-child {{
            border-bottom: none;
        }}
        .label {{
            font-weight: bold;
            color: #555;
        }}
        .value {{
            color: #333;
        }}
        .status {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }}
        .status.uploaded {{
            background-color: #d4edda;
            color: #155724;
        }}
        .status.missing {{
            background-color: #f8d7da;
            color: #721c24;
        }}
        .footer {{
            text-align: center;
            margin-top: 20px;
            padding: 15px;
            background-color: #e9ecef;
            border-radius: 5px;
            font-size: 14px;
            color: #6c757d;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔔 New Check-in Completed</h1>
        <p>A client has completed the check-in process</p>
    </div>

    <div class="content">
        <div class="section">
            <h3>📋 Reservation Details</h3>
            <div class="info-row">
                <span class="label">Reservation Number:</span>
                <span class="value">{checkin_data.get('reservation_number', 'N/A')}</span>
            </div>
            <div class="info-row">
                <span class="label">Guest Name:</span>
                <span class="value">{checkin_data.get('guest_name', 'N/A')}</span>
            </div>
            <div class="info-row">
                <span class="label">Check-in Date:</span>
                <span class="value">{checkin_data.get('start_date', 'N/A')}</span>
            </div>
            <div class="info-row">
                <span class="label">Check-out Date:</span>
                <span class="value">{checkin_data.get('end_date', 'N/A')}</span>
            </div>
            <div class="info-row">
                <span class="label">Room:</span>
                <span class="value">{checkin_data.get('room_name', 'N/A')}</span>
            </div>
        </div>

        <div class="section">
            <h3>👤 Client Information</h3>
            <div class="info-row">
                <span class="label">Name:</span>
                <span class="value">{checkin_data.get('client_name', 'N/A')}</span>
            </div>
            <div class="info-row">
                <span class="label">Surname:</span>
                <span class="value">{checkin_data.get('client_surname', 'N/A')}</span>
            </div>
            <div class="info-row">
                <span class="label">Email:</span>
                <span class="value">{checkin_data.get('client_email', 'N/A')}</span>
            </div>
            <div class="info-row">
                <span class="label">Phone:</span>
                <span class="value">{checkin_data.get('client_phone', 'N/A')}</span>
            </div>
            <div class="info-row">
                <span class="label">Document Type:</span>
                <span class="value">{checkin_data.get('document_type', 'N/A')}</span>
            </div>
            <div class="info-row">
                <span class="label">Document Number:</span>
                <span class="value">{checkin_data.get('document_number', 'N/A')}</span>
            </div>
        </div>

        <div class="section">
            <h3>📄 Uploaded Documents</h3>
            <div class="info-row">
                <span class="label">Front Document:</span>
                <span class="status {'uploaded' if checkin_data.get('has_front_image') else 'missing'}">
                    {'✓ Uploaded' if checkin_data.get('has_front_image') else '✗ Missing'}
                </span>
            </div>
            <div class="info-row">
                <span class="label">Back Document:</span>
                <span class="status {'uploaded' if checkin_data.get('has_back_image') else 'missing'}">
                    {'✓ Uploaded' if checkin_data.get('has_back_image') else '✗ Missing'}
                </span>
            </div>
            <div class="info-row">
                <span class="label">Selfie:</span>
                <span class="status {'uploaded' if checkin_data.get('has_selfie') else 'missing'}">
                    {'✓ Uploaded' if checkin_data.get('has_selfie') else '✗ Missing'}
                </span>
            </div>
        </div>

        <div class="footer">
            <p><strong>Action Required:</strong> Please review the uploaded documents and client information in the admin panel.</p>
            <p>Best regards,<br>Remote Check-in System</p>
        </div>
    </div>
</body>
</html>
        """.strip()


    def send_reservation_approval_notification(
        self,
        client_email: str,
        reservation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send a reservation approval email to the client and return the send result.
        
        Validates the provided client_email (strict validation). Builds a subject using
        reservation_data['reservation_number'] (falls back to 'N/A' if missing) and
        generates both plain-text and HTML bodies via the approval templates, then
        sends the email through the configured provider.
        
        Parameters:
            client_email (str): Recipient email address.
            reservation_data (dict): Reservation details used to populate templates.
                Expected keys (used by templates): 'reservation_number', 'guest_name',
                'start_date', 'end_date', 'room_name' (any missing keys are tolerated
                but may result in placeholders like 'N/A').
        
        Returns:
            dict: Result returned from send_email on success (typically contains
            provider-specific metadata). On failure returns a dict with "status":
            "error" and a "message" describing the validation or send failure.
        """
        try:
            # Validate email address
            validated_email = self.validate_email_address(client_email)

            # Create email subject and body
            subject = f"Reservation Approved - {reservation_data.get('reservation_number', 'N/A')}"
            body = self._create_reservation_approval_text(reservation_data)
            html_body = self._create_reservation_approval_html(reservation_data)

            # Create EmailData object
            email_data = EmailData(
                to_email=validated_email,
                subject=subject,
                body=body,
                html_body=html_body
            )

            # Send email
            return self.send_email(email_data)

        except EmailValidationError as e:
            logger.error("Email validation error: %s", str(e))
            return {"status": "error", "message": f"Invalid email address: {str(e)}"}
        except Exception as e:
            logger.error("Error sending reservation approval notification: %s", str(e))
            return {"status": "error", "message": f"Failed to send approval notification: {str(e)}"}

    def send_reservation_revision_notification(
        self,
        client_email: str,
        reservation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send a "reservation requires revision" notification to a client.
        
        Validates client_email (strict validation), builds text and HTML bodies from reservation_data templates, constructs an EmailData payload, and sends it via the configured provider. Returns a status dictionary with keys like "status" and "message" describing success or failure. The function catches validation errors and other exceptions and returns an error status instead of raising.
        """
        try:
            # Validate email address
            validated_email = self.validate_email_address(client_email)

            # Create email subject and body
            subject = f"Reservation Requires Revision - {reservation_data.get('reservation_number', 'N/A')}"
            body = self._create_reservation_revision_text(reservation_data)
            html_body = self._create_reservation_revision_html(reservation_data)

            # Create EmailData object
            email_data = EmailData(
                to_email=validated_email,
                subject=subject,
                body=body,
                html_body=html_body
            )

            # Send email
            return self.send_email(email_data)

        except EmailValidationError as e:
            logger.error("Email validation error: %s", str(e))
            return {"status": "error", "message": f"Invalid email address: {str(e)}"}
        except Exception as e:
            logger.error("Error sending reservation revision notification: %s", str(e))
            return {"status": "error", "message": f"Failed to send revision notification: {str(e)}"}

    def _create_reservation_approval_text(self, reservation_data: Dict[str, Any]) -> str:
        """
        Return a plain-text reservation approval message populated from reservation_data.
        
        Parameters:
            reservation_data (Dict[str, Any]): Mapping with optional keys:
                - 'guest_name', 'reservation_number', 'start_date', 'end_date', 'room_name'.
                Missing keys are replaced with sensible defaults ('Guest' or 'N/A').
        
        Returns:
            str: Formatted plain-text approval notification suitable for sending as the email body.
        """
        return f"""
Dear {reservation_data.get('guest_name', 'Guest')},

Great news! Your reservation has been approved.

Reservation Details:
- Reservation Number: {reservation_data.get('reservation_number', 'N/A')}
- Check-in Date: {reservation_data.get('start_date', 'N/A')}
- Check-out Date: {reservation_data.get('end_date', 'N/A')}
- Room: {reservation_data.get('room_name', 'N/A')}

Your reservation is now confirmed and ready for your stay. Please keep this email for your records.

If you have any questions or need to make changes, please contact us as soon as possible.

We look forward to welcoming you!

Best regards,
The Management Team
        """.strip()

    def _create_reservation_approval_html(self, reservation_data: Dict[str, Any]) -> str:
        """
        Return an HTML-formatted email body for a reservation approval notification.
        
        The HTML includes a header, a success message, and a reservation details block.
        Expects `reservation_data` to be a mapping containing (optional) keys:
        - 'guest_name' (str): guest display name, defaults to 'Guest'
        - 'reservation_number' (str): reservation identifier, defaults to 'N/A'
        - 'start_date' (str): check-in date, defaults to 'N/A'
        - 'end_date' (str): check-out date, defaults to 'N/A'
        - 'room_name' (str): room name, defaults to 'N/A'
        
        Returns:
            str: Complete HTML string suitable for use as an email body.
        """
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Reservation Approved</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
        .content {{ background-color: #f8f9fa; padding: 20px; border-radius: 0 0 5px 5px; }}
        .reservation-details {{ background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        .info-row {{ display: flex; justify-content: space-between; margin: 10px 0; padding: 5px 0; border-bottom: 1px solid #eee; }}
        .label {{ font-weight: bold; color: #555; }}
        .value {{ color: #333; }}
        .footer {{ margin-top: 20px; padding-top: 15px; border-top: 1px solid #ddd; color: #666; }}
        .success {{ color: #28a745; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎉 Reservation Approved!</h1>
    </div>

    <div class="content">
        <p>Dear <strong>{reservation_data.get('guest_name', 'Guest')}</strong>,</p>

        <p class="success">Great news! Your reservation has been approved and is now confirmed.</p>

        <div class="reservation-details">
            <h3>Reservation Details</h3>
            <div class="info-row">
                <span class="label">Reservation Number:</span>
                <span class="value">{reservation_data.get('reservation_number', 'N/A')}</span>
            </div>
            <div class="info-row">
                <span class="label">Check-in Date:</span>
                <span class="value">{reservation_data.get('start_date', 'N/A')}</span>
            </div>
            <div class="info-row">
                <span class="label">Check-out Date:</span>
                <span class="value">{reservation_data.get('end_date', 'N/A')}</span>
            </div>
            <div class="info-row">
                <span class="label">Room:</span>
                <span class="value">{reservation_data.get('room_name', 'N/A')}</span>
            </div>
        </div>

        <p>Your reservation is now confirmed and ready for your stay. Please keep this email for your records.</p>

        <p>If you have any questions or need to make changes, please contact us as soon as possible.</p>

        <p>We look forward to welcoming you!</p>

        <div class="footer">
            <p>Best regards,<br>The Management Team</p>
        </div>
    </div>
</body>
</html>
        """.strip()

    def _create_reservation_revision_text(self, reservation_data: Dict[str, Any]) -> str:
        """
        Create the plain-text body for a reservation revision notification.
        
        Expected keys in reservation_data (defaults used if missing):
        - reservation_number: reservation identifier (defaults to 'N/A')
        - guest_name: guest display name (defaults to 'Guest')
        - start_date: check-in date (defaults to 'N/A')
        - end_date: check-out date (defaults to 'N/A')
        - room_name: room or unit name (defaults to 'N/A')
        
        Returns:
            str: Formatted plain-text message ready to send to the guest.
        """
        return f"""
Dear {reservation_data.get('guest_name', 'Guest')},

We need to discuss your reservation and may require some revisions.

Reservation Details:
- Reservation Number: {reservation_data.get('reservation_number', 'N/A')}
- Check-in Date: {reservation_data.get('start_date', 'N/A')}
- Check-out Date: {reservation_data.get('end_date', 'N/A')}
- Room: {reservation_data.get('room_name', 'N/A')}

Please contact us as soon as possible to discuss the details of your reservation. We want to ensure everything is perfect for your stay.

We appreciate your understanding and look forward to resolving any questions you may have.

Best regards,
The Management Team
        """.strip()

    def _create_reservation_revision_html(self, reservation_data: Dict[str, Any]) -> str:
        """
        Return an HTML email body for a "reservation requires revision" notification.
        
        The returned HTML includes a styled header, reservation summary, an action block asking the guest to contact management, and a footer. The function reads these keys from reservation_data (all optional; defaults shown in the output):
        - 'guest_name'
        - 'reservation_number'
        - 'start_date'
        - 'end_date'
        - 'room_name'
        
        Returns:
            str: Complete HTML document as a string.
        """
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Reservation Requires Revision</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #ffc107; color: #333; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
        .content {{ background-color: #f8f9fa; padding: 20px; border-radius: 0 0 5px 5px; }}
        .reservation-details {{ background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        .info-row {{ display: flex; justify-content: space-between; margin: 10px 0; padding: 5px 0; border-bottom: 1px solid #eee; }}
        .label {{ font-weight: bold; color: #555; }}
        .value {{ color: #333; }}
        .footer {{ margin-top: 20px; padding-top: 15px; border-top: 1px solid #ddd; color: #666; }}
        .warning {{ color: #ffc107; font-weight: bold; }}
        .action {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📋 Reservation Requires Revision</h1>
    </div>

    <div class="content">
        <p>Dear <strong>{reservation_data.get('guest_name', 'Guest')}</strong>,</p>

        <p class="warning">We need to discuss your reservation and may require some revisions.</p>

        <div class="reservation-details">
            <h3>Reservation Details</h3>
            <div class="info-row">
                <span class="label">Reservation Number:</span>
                <span class="value">{reservation_data.get('reservation_number', 'N/A')}</span>
            </div>
            <div class="info-row">
                <span class="label">Check-in Date:</span>
                <span class="value">{reservation_data.get('start_date', 'N/A')}</span>
            </div>
            <div class="info-row">
                <span class="label">Check-out Date:</span>
                <span class="value">{reservation_data.get('end_date', 'N/A')}</span>
            </div>
            <div class="info-row">
                <span class="label">Room:</span>
                <span class="value">{reservation_data.get('room_name', 'N/A')}</span>
            </div>
        </div>

        <div class="action">
            <p><strong>Action Required:</strong> Please contact us as soon as possible to discuss the details of your reservation. We want to ensure everything is perfect for your stay.</p>
        </div>

        <p>We appreciate your understanding and look forward to resolving any questions you may have.</p>

        <div class="footer">
            <p>Best regards,<br>The Management Team</p>
        </div>
    </div>
</body>
</html>
        """.strip()


# Legacy function for backward compatibility
def send_reservation_email(client_email: str, reservation_details: str, user_id: int = None) -> dict:
    """
    Send a reservation confirmation using legacy behavior for backward compatibility.
    
    This convenience wrapper looks up the active EmailConfig for the given user_id, builds a minimal reservation_data dictionary (attempting to extract a reservation number from reservation_details when the pattern "Reservation #<number>" appears), creates an EmailService using the user's configuration and encryption key, and forwards a reservation confirmation to client_email. Intended only for legacy callers; new code should use EmailService directly.
    
    Parameters:
        client_email (str): Recipient email address.
        reservation_details (str): Free-form reservation string; if it contains "Reservation #<number>" the number will be extracted.
        user_id (int, optional): Required user identifier used to find the user's email configuration in the database.
    
    Returns:
        dict: Result object with at least a "status" key ("success" or "error") and a "message" or provider-specific details. On failure this function returns an error dict rather than raising.
    """
    try:
        logger.warning("Using legacy send_reservation_email function. Consider using EmailService instead.")

        if not user_id:
            return {"status": "error", "message": "User ID is required for email configuration"}

        # Create a basic reservation data structure
        reservation_data = {
            'reservation_number': 'N/A',
            'guest_name': 'Guest',
            'start_date': 'N/A',
            'end_date': 'N/A',
            'room_name': 'N/A'
        }

        # Try to extract information from reservation_details string
        if 'Reservation #' in reservation_details:
            # Extract reservation number
            match = re.search(r'Reservation #(\d+)', reservation_details)
            if match:
                reservation_data['reservation_number'] = match.group(1)

        # Get email configuration from database

        session = SessionLocal()
        try:
            email_config = session.query(EmailConfig).filter(
                EmailConfig.user_id == user_id,
                EmailConfig.is_active.is_(True)
            ).first()

            if not email_config:
                return {"status": "error", "message": "No email configuration found for user"}

            encryption_key = get_encryption_key()
            email_service = EmailService(config=email_config, encryption_key=encryption_key)

            return email_service.send_reservation_confirmation(client_email, reservation_data)

        finally:
            session.close()

    except Exception as e:
        logger.error("Error in legacy send_reservation_email: %s", str(e))
        return {"status": "error", "message": str(e)}
