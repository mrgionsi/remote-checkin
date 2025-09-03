# Email Configuration Guide

This document explains how to configure email functionality in the remote check-in system.

## Environment Variables

The following environment variables are required for email functionality:

### Required Variables

- `MAIL_SERVER`: SMTP server address (e.g., smtp.gmail.com)
- `MAIL_PORT`: SMTP server port (e.g., 587 for TLS, 465 for SSL)
- `MAIL_USERNAME`: Your email username/address
- `MAIL_PASSWORD`: Your email password or app-specific password
- `MAIL_DEFAULT_SENDER_EMAIL`: Default sender email address

### Optional Variables

- `MAIL_USE_TLS`: Enable TLS (default: True)
- `MAIL_USE_SSL`: Enable SSL (default: False)
- `MAIL_DEFAULT_SENDER_NAME`: Default sender name (default: "Remote Check-in System")
- `MAIL_MAX_EMAILS`: Maximum emails per connection (default: 100)
- `MAIL_ASCII_ATTACHMENTS`: Use ASCII attachments (default: False)

## Gmail Configuration

To use Gmail as your SMTP server:

1. Enable 2-factor authentication on your Google account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a password for "Mail"
3. Use the generated password as `MAIL_PASSWORD`

Example Gmail configuration:

```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_DEFAULT_SENDER_EMAIL=your_email@gmail.com
```

## Other SMTP Providers

### Outlook/Hotmail

```bash
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USE_TLS=True
```

### Yahoo

```bash
MAIL_SERVER=smtp.mail.yahoo.com
MAIL_PORT=587
MAIL_USE_TLS=True
```

### Custom SMTP Server

```bash
MAIL_SERVER=your.smtp.server.com
MAIL_PORT=587
MAIL_USE_TLS=True
```

## Testing Configuration

For testing purposes, you can use a local SMTP server like MailHog:

```bash
MAIL_SERVER=localhost
MAIL_PORT=1025
MAIL_USE_TLS=False
MAIL_USE_SSL=False
MAIL_USERNAME=test@example.com
MAIL_PASSWORD=test_password
```

## Security Notes

1. **Never commit email passwords to version control**
2. **Use environment variables for all sensitive configuration**
3. **Consider using app-specific passwords for third-party services**
4. **Enable TLS/SSL when possible for secure communication**
5. **Regularly rotate passwords and app-specific keys**

## Troubleshooting

### Common Issues

1. **Authentication failed**: Check username/password and ensure 2FA is properly configured
2. **Connection refused**: Verify server address and port
3. **TLS/SSL errors**: Ensure the correct protocol is enabled for your server
4. **Rate limiting**: Some providers limit emails per day/hour

### Debug Mode

Enable debug logging by setting the log level:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing Email Service

You can test the email service using the provided test methods:

```python
from email_handler import EmailService

# Test email validation
email_service = EmailService(mail_instance)
result = email_service.validate_email_address("test@example.com")
print(result)
```
