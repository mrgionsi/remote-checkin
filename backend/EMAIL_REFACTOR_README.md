# Email System Refactor - Database-Driven Configuration

## Overview

The email system has been completely refactored from environment variable-based configuration to a user-specific, database-driven system. This allows each user to configure their own email settings, supports multiple email providers, and provides better security and flexibility.

## Key Changes

### 1. Database Schema Changes

#### New EmailConfig Table

```sql
CREATE TABLE email_config (
  id INTEGER PRIMARY KEY DEFAULT nextval('email_config_id_seq'),
  user_id BIGINT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
  mail_server VARCHAR NOT NULL,
  mail_port INTEGER NOT NULL,
  mail_use_tls BOOLEAN NOT NULL DEFAULT TRUE,
  mail_use_ssl BOOLEAN NOT NULL DEFAULT FALSE,
  mail_username VARCHAR NOT NULL,
  mail_password VARCHAR NOT NULL,  -- Encrypted
  mail_default_sender_name VARCHAR,
  mail_default_sender_email VARCHAR NOT NULL,
  provider_type VARCHAR NOT NULL DEFAULT 'smtp',
  provider_config TEXT,  -- JSON string for provider-specific settings
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
  updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

-- One-to-one relationship with users
CREATE UNIQUE INDEX ux_email_config_user_id ON email_config(user_id);
```

#### Updated Reservation Table

```sql
-- Added email and telephone fields to reservation table
ALTER TABLE reservation
  ADD COLUMN email VARCHAR DEFAULT '' NOT NULL,
  ADD COLUMN telephone VARCHAR DEFAULT '' NOT NULL;
```

### 2. Backend Changes

#### EmailService Class Refactor

- **Removed**: Environment variable dependencies
- **Removed**: Flask-Mail instance creation and manipulation
- **Added**: Direct `smtplib` usage for SMTP
- **Added**: Database configuration support
- **Added**: Password encryption/decryption
- **Added**: Multiple provider support (SMTP, Mailgun, SendGrid)

#### New Email Configuration Routes

- `GET /api/v1/email-config` - Get user's email configuration
- `POST /api/v1/email-config` - Create/update email configuration
- `POST /api/v1/email-config/test` - Test email configuration
- `DELETE /api/v1/email-config` - Delete email configuration
- `GET /api/v1/email-config/presets` - Get provider presets
- `GET /api/v1/email-config/preset/<name>` - Get specific preset
- `POST /api/v1/email-config/migrate` - Migrate to external provider

#### Updated Reservation Routes

- Now uses database email configuration instead of environment variables
- Requires email configuration to be set before sending emails
- Uses user-specific email settings

### 3. Frontend Changes

#### New Email Settings Component

- Integrated into the main Settings page
- Form for configuring SMTP settings
- Provider preset selection (Gmail, Outlook, Yahoo, Mailgun, SendGrid, Custom)
- Test email functionality
- Save/load configuration

#### Updated Translation Files

- Added email-related translation keys in `en.json` and `it.json`
- Email field labels, placeholders, and validation messages

#### Updated Reservation Forms

- Added email and telephone fields to create reservation form
- Added email and telephone display/edit in reservation details
- Form validation for email fields

### 4. Security Improvements

#### Password Encryption

- Email passwords are encrypted using Fernet encryption
- Encryption key stored in Flask app configuration
- Automatic key generation if not present

#### User Isolation

- Each user has their own email configuration
- No shared email settings between users
- Database-level user isolation

### 5. Email Provider Support

#### SMTP (Default)

- Direct `smtplib` usage
- Support for TLS/SSL
- Custom SMTP server configuration

#### Mailgun

- API-based email sending
- Domain and API key configuration
- JSON configuration storage

#### SendGrid

- API-based email sending
- API key configuration
- JSON configuration storage

### 6. Email Formatting

#### Sender Name Format

- Format: `"Remote Check-in System ('{sender_name}')"`
- Example: `"Remote Check-in System ('B&B Chapeau')"`
- Consistent across all providers

#### Email Templates

- HTML and plain text versions
- Reservation confirmation, update, and cancellation templates
- Responsive HTML design

## Migration Guide

### For Existing Users

1. **Database Migration**: Run the SQL migration script to create the `email_config` table
2. **User Configuration**: Each user must configure their email settings through the frontend
3. **Environment Variables**: Remove email-related environment variables (optional)

### SQL Migration Script

```sql
BEGIN;

-- Add email and telephone to reservation table
ALTER TABLE reservation
  ADD COLUMN IF NOT EXISTS email VARCHAR DEFAULT '' NOT NULL,
  ADD COLUMN IF NOT EXISTS telephone VARCHAR DEFAULT '' NOT NULL;

-- Create email_config table
CREATE SEQUENCE IF NOT EXISTS email_config_id_seq;

CREATE TABLE IF NOT EXISTS email_config (
  id INTEGER PRIMARY KEY DEFAULT nextval('email_config_id_seq'),
  user_id BIGINT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
  mail_server VARCHAR NOT NULL,
  mail_port INTEGER NOT NULL,
  mail_use_tls BOOLEAN NOT NULL DEFAULT TRUE,
  mail_use_ssl BOOLEAN NOT NULL DEFAULT FALSE,
  mail_username VARCHAR NOT NULL,
  mail_password VARCHAR NOT NULL,
  mail_default_sender_name VARCHAR,
  mail_default_sender_email VARCHAR NOT NULL,
  provider_type VARCHAR NOT NULL DEFAULT 'smtp',
  provider_config TEXT,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
  updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

-- Create indexes and constraints
CREATE UNIQUE INDEX IF NOT EXISTS ux_email_config_user_id ON email_config(user_id);
CREATE INDEX IF NOT EXISTS ix_email_config_is_active ON email_config(is_active);
CREATE INDEX IF NOT EXISTS ix_email_config_provider_type ON email_config(provider_type);

COMMIT;
```

## Usage Examples

### 1. Configure Email Settings (Frontend)

1. Navigate to Settings page
2. Scroll to "Email Configuration" section
3. Select a provider preset or configure custom SMTP
4. Fill in required fields (server, port, username, password, sender email)
5. Test the configuration
6. Save the settings

### 2. Send Test Email (API)

```bash
curl -X POST http://localhost:5000/api/v1/email-config/test \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"test_email": "test@example.com"}'
```

### 3. Create Email Configuration (API)

```bash
curl -X POST http://localhost:5000/api/v1/email-config \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "mail_server": "smtp.gmail.com",
    "mail_port": 587,
    "mail_use_tls": true,
    "mail_use_ssl": false,
    "mail_username": "user@gmail.com",
    "mail_password": "app_password",
    "mail_default_sender_name": "B&B Chapeau",
    "mail_default_sender_email": "user@gmail.com",
    "provider_type": "smtp"
  }'
```

## Provider Presets

### Gmail

- Server: `smtp.gmail.com`
- Port: `587`
- TLS: `true`
- SSL: `false`
- Note: Requires App Password

### Outlook/Hotmail

- Server: `smtp-mail.outlook.com`
- Port: `587`
- TLS: `true`
- SSL: `false`

### Yahoo

- Server: `smtp.mail.yahoo.com`
- Port: `587`
- TLS: `true`
- SSL: `false`
- Note: Requires App Password

### Mailgun

- Provider Type: `mailgun`
- Requires domain and API key in provider_config

### SendGrid

- Provider Type: `sendgrid`
- Requires API key in provider_config

## Troubleshooting

### Common Issues

1. **"No email configuration found"**

   - User must configure email settings in the frontend
   - Check if user has an active email configuration in database

2. **"Failed to decrypt password"**

   - Check if ENCRYPTION_KEY is set in Flask app config
   - Key is automatically generated if not present

3. **SMTP Authentication Failed**

   - Verify username and password
   - For Gmail, use App Password instead of regular password
   - Check if 2FA is enabled and App Password is generated

4. **Email not received**
   - Check spam/junk folders
   - Verify sender email format
   - Test with different email providers

### Debug Steps

1. **Check Database Configuration**

   ```sql
   SELECT * FROM email_config WHERE user_id = <user_id> AND is_active = true;
   ```

2. **Test Email Configuration**

   - Use the test endpoint in the frontend
   - Check application logs for detailed error messages

3. **Verify Provider Settings**
   - For external providers, verify API keys and domains
   - Check provider-specific documentation

## Future Enhancements

1. **Email Templates Management**

   - User-customizable email templates
   - Template editor in frontend

2. **Email Analytics**

   - Track email delivery status
   - Bounce and open rate monitoring

3. **Bulk Email Support**

   - Send emails to multiple recipients
   - Email campaigns

4. **Advanced Security**

   - OAuth2 authentication for email providers
   - Certificate-based authentication

5. **Email Scheduling**
   - Schedule emails for future delivery
   - Recurring email notifications

## Breaking Changes

1. **Environment Variables**: Email-related environment variables are no longer used
2. **EmailService Constructor**: Now requires EmailConfig instance instead of mail instance
3. **User Requirements**: All users must configure email settings before sending emails
4. **Database Schema**: New tables and columns added

## Dependencies

### New Dependencies

- `cryptography` - For password encryption
- `requests` - For external provider APIs

### Updated Dependencies

- All existing dependencies remain the same

## Testing

### Unit Tests

- EmailService with database configuration
- Email validation and formatting
- Provider-specific sending methods

### Integration Tests

- End-to-end email sending
- Configuration management
- Error handling scenarios

### Manual Testing

- Use the email test utility: `python email_test_utility.py`
- Test with different email providers
- Verify email delivery and formatting
