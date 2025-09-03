"""
Email handling module for the remote check-in system.

This module provides a comprehensive email service for sending various types of emails
including reservation confirmations, updates, and cancellations.
"""

import logging
import re
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from flask import current_app
from flask_mail import Message, Mail
from email_validator import validate_email, EmailNotValidError
import requests

from models import EmailConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
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
        
        Args:
            config: EmailConfig instance (for database configuration)
            encryption_key: Encryption key for decrypting passwords
        """
        if not config:
            raise EmailServiceError("EmailConfig is required")
            
        self.config = config
        self.encryption_key = encryption_key
        self.provider_type = config.provider_type or 'smtp'
        self.provider_config = json.loads(config.provider_config) if config.provider_config else {}
        
        self._setup_from_config()
    
    def _setup_from_config(self) -> None:
        """Setup email service from database configuration."""
        if not self.config:
            raise EmailServiceError("No configuration provided")
        
        # Store the decrypted password for use in sending emails
        self.decrypted_password = self._decrypt_password(self.config.mail_password)
        
        # We don't need to create a Flask app - we'll use the existing one
        # and override the mail configuration when sending emails
    
    def _decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt password from database."""
        try:
            from cryptography.fernet import Fernet
            
            # Use encryption key passed to constructor, or try to get from current app context
            key = self.encryption_key
            if not key:
                try:
                    key = current_app.config.get('EMAIL_ENCRYPTION_KEY')
                except RuntimeError:
                    # current_app is not available in this context
                    logger.warning("No Flask app context available for decryption")
            
            if not key:
                # If no encryption key, assume password is not encrypted (for backward compatibility)
                logger.info("No encryption key found, using password as-is")
                return encrypted_password
            
            f = Fernet(key)
            return f.decrypt(encrypted_password.encode()).decode()
        except Exception as e:
            logger.warning(f"Failed to decrypt password, using as-is: {str(e)}")
            return encrypted_password
    
    def validate_email_address(self, email: str) -> str:
        """
        Validate an email address.
        
        Args:
            email: Email address to validate
            
        Returns:
            Normalized email address
            
        Raises:
            EmailValidationError: If email is invalid
        """
        try:
            # Validate and normalize email
            validated_email = validate_email(email, check_deliverability=False)
            return validated_email.normalized
        except EmailNotValidError as e:
            raise EmailValidationError(f"Invalid email address: {str(e)}")
    
    def validate_email_address_lenient(self, email: str) -> str:
        """
        Validate an email address with more lenient rules.
        
        Args:
            email: Email address to validate
            
        Returns:
            Email address (cleaned but not strictly validated)
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
        Validate a list of email addresses.
        
        Args:
            emails: List of email addresses to validate
            
        Returns:
            List of normalized email addresses
            
        Raises:
            EmailValidationError: If any email is invalid
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
        Send an email using the configured provider.
        
        Args:
            email_data: EmailData object containing email information
            
        Returns:
            Dictionary with status and message
        """
        try:
            logger.info(f"Preparing to send email to: {email_data.to_email} using {self.provider_type}")
            
            # Route to appropriate provider
            if self.provider_type == 'mailgun':
                return self._send_via_mailgun(email_data)
            elif self.provider_type == 'sendgrid':
                return self._send_via_sendgrid(email_data)
            else:
                # Default to SMTP
                return self._send_via_smtp(email_data)
            
        except EmailValidationError as e:
            logger.error(f"Email validation error: {str(e)}")
            return {
                "status": "error",
                "message": f"Email validation failed: {str(e)}",
                "error_type": "validation_error"
            }
        except Exception as e:
            logger.error(f"Failed to send email to {email_data.to_email}: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to send email: {str(e)}",
                "error_type": "send_error"
            }
    
    def _send_via_smtp(self, email_data: EmailData) -> Dict[str, Any]:
        """Send email via SMTP using smtplib directly."""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.utils import formataddr
        
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
                    from email.mime.base import MIMEBase
                    from email import encoders
                    
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['data'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment["filename"]}'
                    )
                    msg.attach(part)
            
            # Connect to SMTP server
            if self.config.mail_use_ssl:
                server = smtplib.SMTP_SSL(self.config.mail_server, self.config.mail_port)
            else:
                server = smtplib.SMTP(self.config.mail_server, self.config.mail_port)
                if self.config.mail_use_tls:
                    server.starttls()
            
            # Login and send
            server.login(self.config.mail_username, self.decrypted_password)
            
            # Prepare recipients list
            recipients = [email_data.to_email]
            if email_data.cc:
                recipients.extend(email_data.cc)
            if email_data.bcc:
                recipients.extend(email_data.bcc)
            
            server.send_message(msg, to_addrs=recipients)
            server.quit()
            
            logger.info(f"Email sent successfully via SMTP to: {email_data.to_email}")
            return {
                "status": "success",
                "message": "Email sent successfully",
                "to": email_data.to_email,
                "subject": email_data.subject,
                "provider": "smtp"
            }
            
        except Exception as e:
            logger.error(f"SMTP error: {str(e)}")
            raise EmailServiceError(f"Failed to send email via SMTP: {str(e)}")
    
    def _send_via_mailgun(self, email_data: EmailData) -> Dict[str, Any]:
        """Send email via Mailgun API."""
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
            logger.info(f"Email sent successfully via Mailgun to: {email_data.to_email}")
            return {
                "status": "success",
                "message": "Email sent successfully via Mailgun",
                "to": email_data.to_email,
                "subject": email_data.subject,
                "provider": "mailgun",
                "response": response.json()
            }
        else:
            raise EmailServiceError(f"Mailgun API error: {response.status_code} - {response.text}")
    
    def _send_via_sendgrid(self, email_data: EmailData) -> Dict[str, Any]:
        """Send email via SendGrid API."""
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
                "name": f"Remote Check-in System ('{self.config.mail_default_sender_name if self.config.mail_default_sender_name and self.config.mail_default_sender_name.strip() else 'Remote Check-in'}')"
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
            logger.info(f"Email sent successfully via SendGrid to: {email_data.to_email}")
            return {
                "status": "success",
                "message": "Email sent successfully via SendGrid",
                "to": email_data.to_email,
                "subject": email_data.subject,
                "provider": "sendgrid"
            }
        else:
            raise EmailServiceError(f"SendGrid API error: {response.status_code} - {response.text}")
    
    def send_reservation_confirmation(
        self, 
        client_email: str, 
        reservation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send a reservation confirmation email.
        
        Args:
            client_email: Client's email address
            reservation_data: Dictionary containing reservation information
            
        Returns:
            Dictionary with status and message
        """
        try:
            # Validate client email first
            try:
                validated_email = self.validate_email_address(client_email)
                logger.info(f"Email validation successful: {client_email} -> {validated_email}")
            except EmailValidationError as e:
                logger.warning(f"Strict email validation failed for {client_email}: {str(e)}")
                # Try lenient validation as fallback
                try:
                    validated_email = self.validate_email_address_lenient(client_email)
                    logger.info(f"Lenient email validation successful: {client_email} -> {validated_email}")
                except EmailValidationError as e2:
                    logger.error(f"Both strict and lenient email validation failed for {client_email}: {str(e2)}")
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
            
            logger.info(f"Sending reservation confirmation to: {validated_email}")
            return self.send_email(email_data)
            
        except Exception as e:
            logger.error(f"Error creating reservation confirmation email: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
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
        Send a reservation update email.
        
        Args:
            client_email: Client's email address
            reservation_data: Dictionary containing updated reservation information
            
        Returns:
            Dictionary with status and message
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
            logger.error(f"Error creating reservation update email: {str(e)}")
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
        Send a reservation cancellation email.
        
        Args:
            client_email: Client's email address
            reservation_data: Dictionary containing cancelled reservation information
            
        Returns:
            Dictionary with status and message
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
            logger.error(f"Error creating reservation cancellation email: {str(e)}")
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
        """Create HTML body for reservation confirmation."""
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
        """Create plain text body for reservation update."""
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
        """Create HTML body for reservation update."""
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
        """Create plain text body for reservation cancellation."""
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
        """Create HTML body for reservation cancellation."""
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
                logger.info(f"Admin email validation successful: {admin_email} -> {validated_email}")
            except EmailValidationError as e:
                logger.warning(f"Strict email validation failed for admin {admin_email}: {str(e)}")
                # Try lenient validation as fallback
                try:
                    validated_email = self.validate_email_address_lenient(admin_email)
                    logger.info(f"Lenient admin email validation successful: {admin_email} -> {validated_email}")
                except EmailValidationError as e2:
                    logger.error(f"Both strict and lenient email validation failed for admin {admin_email}: {str(e2)}")
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
            
            logger.info(f"Sending admin check-in notification to: {validated_email}")
            return self.send_email(email_data)
            
        except Exception as e:
            logger.error(f"Error creating admin check-in notification email: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "status": "error",
                "message": f"Error creating admin notification email: {str(e)}",
                "error_type": "creation_error"
            }

    def _create_admin_checkin_notification_text(self, checkin_data: Dict[str, Any]) -> str:
        """Create plain text version of admin check-in notification email."""
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
        """Create HTML version of admin check-in notification email."""
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


# Legacy function for backward compatibility
def send_reservation_email(client_email: str, reservation_details: str, user_id: int = None) -> dict:
    """
    Legacy function for backward compatibility.
    
    Args:
        client_email: Client's email address
        reservation_details: Reservation details as string
        user_id: User ID to get email configuration from database
        
    Returns:
        Dictionary with status and message
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
            import re
            match = re.search(r'Reservation #(\d+)', reservation_details)
            if match:
                reservation_data['reservation_number'] = match.group(1)
        
        # Get email configuration from database
        from models import EmailConfig
        from database import SessionLocal
        from routes.email_config_routes import get_encryption_key
        
        session = SessionLocal()
        try:
            email_config = session.query(EmailConfig).filter(
                EmailConfig.user_id == user_id,
                EmailConfig.is_active == True
            ).first()
            
            if not email_config:
                return {"status": "error", "message": "No email configuration found for user"}
            
            encryption_key = get_encryption_key()
            email_service = EmailService(config=email_config, encryption_key=encryption_key)
            
            return email_service.send_reservation_confirmation(client_email, reservation_data)
            
        finally:
            session.close()
        
    except Exception as e:
        logger.error(f"Error in legacy send_reservation_email: {str(e)}")
        return {"status": "error", "message": str(e)}
