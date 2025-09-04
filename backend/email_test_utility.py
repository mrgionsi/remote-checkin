#!/usr/bin/env python3
"""
Email Test Utility

This script provides a simple way to test email functionality during development.
It can be used to send test emails using database configuration.
"""

import os
from dotenv import load_dotenv
from flask import Flask
from email_handler import EmailService, EmailData
from models import EmailConfig
from database import SessionLocal
from routes.email_config_routes import get_encryption_key

# Load environment variables
load_dotenv()

def create_test_app():
    """Create a minimal Flask app for testing."""
    app = Flask(__name__)

    # Configure database connection
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/remotecheckin')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    return app

def get_user_email_config(user_id: int):
    """Get email configuration for a user from database."""
    session = SessionLocal()
    try:
        config = session.query(EmailConfig).filter(
            EmailConfig.user_id == user_id,
            EmailConfig.is_active == True
        ).first()
        return config
    finally:
        session.close()

def test_basic_email():
    """Test sending a basic email."""
    print("Testing basic email functionality...")

    # Get user ID
    user_id = int(input("Enter user ID: "))

    app = create_test_app()
    with app.app_context():
        # Get email configuration from database
        email_config = get_user_email_config(user_id)
        if not email_config:
            print(f"❌ No email configuration found for user {user_id}")
            return {"status": "error", "message": "No email configuration found"}

        encryption_key = get_encryption_key()
        email_service = EmailService(config=email_config, encryption_key=encryption_key)

        email_data = EmailData(
            to_email=input("Enter recipient email: "),
            subject="Test Email from Remote Check-in System",
            body="This is a test email to verify the email service is working correctly.",
            html_body="""
            <html>
                <body>
                    <h2>Test Email</h2>
                    <p>This is a <strong>test email</strong> to verify the email service is working correctly.</p>
                    <p>If you receive this, the email configuration is working!</p>
                </body>
            </html>
            """
        )

        result = email_service.send_email(email_data)
        print(f"Email result: {result}")

        return result

def test_reservation_confirmation():
    """Test sending a reservation confirmation email."""
    print("Testing reservation confirmation email...")

    # Get user ID
    user_id = int(input("Enter user ID: "))

    app = create_test_app()
    with app.app_context():
        # Get email configuration from database
        email_config = get_user_email_config(user_id)
        if not email_config:
            print(f"❌ No email configuration found for user {user_id}")
            return {"status": "error", "message": "No email configuration found"}

        encryption_key = get_encryption_key()
        email_service = EmailService(config=email_config, encryption_key=encryption_key)

        # Get test data
        recipient_email = input("Enter recipient email: ")
        reservation_number = input("Enter reservation number (or press Enter for default): ") or "TEST123"
        guest_name = input("Enter guest name (or press Enter for default): ") or "Test Guest"
        start_date = input("Enter start date (YYYY-MM-DD) (or press Enter for default): ") or "2024-01-01"
        end_date = input("Enter end date (YYYY-MM-DD) (or press Enter for default): ") or "2024-01-03"
        room_name = input("Enter room name (or press Enter for default): ") or "Test Room"

        reservation_data = {
            'reservation_number': reservation_number,
            'guest_name': guest_name,
            'start_date': start_date,
            'end_date': end_date,
            'room_name': room_name
        }

        result = email_service.send_reservation_confirmation(recipient_email, reservation_data)
        print(f"Reservation confirmation result: {result}")

        return result

def test_email_validation():
    """Test email validation functionality."""
    print("Testing email validation...")

    # Get user ID
    user_id = int(input("Enter user ID: "))

    app = create_test_app()
    with app.app_context():
        # Get email configuration from database
        email_config = get_user_email_config(user_id)
        if not email_config:
            print(f"❌ No email configuration found for user {user_id}")
            return

        encryption_key = get_encryption_key()
        email_service = EmailService(config=email_config, encryption_key=encryption_key)

        test_emails = [
            "test@example.com",
            "invalid-email",
            "user@domain.co.uk",
            "another.invalid.email",
            "valid+tag@example.org"
        ]

        for email in test_emails:
            try:
                validated = email_service.validate_email_address(email)
                print(f"✓ {email} -> {validated}")
            except Exception as e:
                print(f"✗ {email} -> {e}")

        # Test email list validation
        print("\nTesting email list validation...")
        try:
            valid_list = email_service.validate_email_list(["test1@example.com", "test2@example.com"])
            print(f"✓ Valid list: {valid_list}")
        except Exception as e:
            print(f"✗ List validation failed: {e}")

def test_admin_checkin_notification():
    """Test sending admin check-in notification email."""
    print("Testing admin check-in notification email...")

    # Get user ID
    user_id = int(input("Enter user ID: "))

    app = create_test_app()
    with app.app_context():
        # Get email configuration from database
        email_config = get_user_email_config(user_id)
        if not email_config:
            print(f"❌ No email configuration found for user {user_id}")
            return {"status": "error", "message": "No email configuration found"}

        encryption_key = get_encryption_key()
        email_service = EmailService(config=email_config, encryption_key=encryption_key)

        # Get test data
        admin_email = input("Enter admin email: ")
        reservation_number = input("Enter reservation number (or press Enter for default): ") or "TEST123"
        guest_name = input("Enter guest name (or press Enter for default): ") or "Test Guest"
        client_name = input("Enter client first name (or press Enter for default): ") or "Test"
        client_surname = input("Enter client last name (or press Enter for default): ") or "Client"
        client_email = input("Enter client email (or press Enter for default): ") or "client@example.com"
        client_phone = input("Enter client phone (or press Enter for default): ") or "+1234567890"
        document_type = input("Enter document type (or press Enter for default): ") or "Passport"
        document_number = input("Enter document number (or press Enter for default): ") or "AB123456"

        checkin_data = {
            'reservation_number': reservation_number,
            'guest_name': guest_name,
            'start_date': '2024-01-01',
            'end_date': '2024-01-03',
            'room_name': 'Test Room',
            'client_name': client_name,
            'client_surname': client_surname,
            'client_email': client_email,
            'client_phone': client_phone,
            'document_type': document_type,
            'document_number': document_number,
            'has_front_image': True,
            'has_back_image': True,
            'has_selfie': True
        }

        result = email_service.send_admin_checkin_notification(admin_email, checkin_data)
        print(f"Admin check-in notification result: {result}")

        return result

def test_reservation_status_notifications():
    """Test sending reservation status notification emails."""
    print("Testing reservation status notification emails...")

    # Get user ID
    user_id = int(input("Enter user ID: "))

    app = create_test_app()
    with app.app_context():
        # Get email configuration from database
        email_config = get_user_email_config(user_id)
        if not email_config:
            print(f"❌ No email configuration found for user {user_id}")
            return {"status": "error", "message": "No email configuration found"}

        encryption_key = get_encryption_key()
        email_service = EmailService(config=email_config, encryption_key=encryption_key)

        # Get test data
        client_email = input("Enter client email: ")
        reservation_number = input("Enter reservation number (or press Enter for default): ") or "TEST123"
        guest_name = input("Enter guest name (or press Enter for default): ") or "Test Guest"

        reservation_data = {
            'reservation_number': reservation_number,
            'guest_name': guest_name,
            'start_date': '2024-01-01',
            'end_date': '2024-01-03',
            'room_name': 'Test Room'
        }

        print("\n1. Testing approval notification...")
        approval_result = email_service.send_reservation_approval_notification(client_email, reservation_data)
        print(f"Approval notification result: {approval_result}")

        print("\n2. Testing revision notification...")
        revision_result = email_service.send_reservation_revision_notification(client_email, reservation_data)
        print(f"Revision notification result: {revision_result}")

        return {
            "approval": approval_result,
            "revision": revision_result
        }

def main():
    """Main function to run email tests."""
    print("Email Test Utility for Remote Check-in System")
    print("=" * 50)
    print("Note: This utility now uses database email configuration.")
    print("Make sure you have configured email settings in the database first.")
    print("=" * 50)

    print("Available tests:")
    print("1. Basic email test")
    print("2. Reservation confirmation email test")
    print("3. Email validation test")
    print("4. Admin check-in notification test")
    print("5. Reservation status notifications test")
    print("6. Run all tests")

    choice = input("\nSelect a test (1-6): ").strip()

    try:
        if choice == "1":
            test_basic_email()
        elif choice == "2":
            test_reservation_confirmation()
        elif choice == "3":
            test_email_validation()
        elif choice == "4":
            test_admin_checkin_notification()
        elif choice == "5":
            test_reservation_status_notifications()
        elif choice == "6":
            print("\nRunning all tests...")
            test_email_validation()
            print("\n" + "="*50 + "\n")
            test_basic_email()
            print("\n" + "="*50 + "\n")
            test_reservation_confirmation()
            print("\n" + "="*50 + "\n")
            test_admin_checkin_notification()
            print("\n" + "="*50 + "\n")
            test_reservation_status_notifications()
        else:
            print("Invalid choice. Please select 1-6.")

    except KeyboardInterrupt:
        print("\n\nTest cancelled by user.")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        print("Please check your email configuration and try again.")

if __name__ == "__main__":
    main()
