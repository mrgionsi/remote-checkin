# Configuration

The Remote Check-in system offers extensive configuration options through environment variables. Keep reading the sub sections for the several configuration supported.

### Database Configuration

- **DB_HOST**: Database server address (default: localhost)
- **DB_PORT**: Database port (default: 5432)
- **DB_USER**: Database username
- **DB_PASSWORD**: Database password
- **DB_NAME**: Database name (default: remotecheckin)
- **DATABASE_TYPE**: Database type (postgresql, mysql, sqlite)

### Security Configuration

- **JWT_SECRET_KEY**: Secret key for JWT tokens (REQUIRED, minimum 16 chars)
- **JWT_ACCESS_TOKEN_EXPIRES**: Access token expiration (default: 3600 seconds)
- **JWT_REFRESH_TOKEN_EXPIRES**: Refresh token expiration (default: 2592000 seconds)

### Email Configuration

- **MAIL_SERVER**: SMTP server address (e.g., smtp.gmail.com)
- **MAIL_PORT**: SMTP port (587 for TLS, 465 for SSL)
- **MAIL_USERNAME**: Email username
- **MAIL_PASSWORD**: Email password or app-specific password
- **MAIL_DEFAULT_SENDER_EMAIL**: Default sender email
- **MAIL_DEFAULT_SENDER_NAME**: Default sender name
- **MAIL_USE_TLS**: Enable TLS (default: True)
- **MAIL_USE_SSL**: Enable SSL (default: False)
- **EMAIL_ENCRYPTION_KEY**: Fernet encryption key for email password encryption (generate with `python backend/generate_encryption_key.py`)

### Application Settings

- **UPLOAD_FOLDER**: Directory for file uploads (default: uploads)
- **MAX_CONTENT_LENGTH**: Maximum file size in bytes (default: 16MB)
- **ALLOWED_CORS**: Allowed CORS origins (comma-separated)
- **DEBUG**: Enable debug mode (default: False)

### File Upload Configuration

The system supports secure file uploads with:

- Document type validation (passport, ID card, driver's license)
- Image format validation (JPEG, PNG)
- File size limits (configurable via MAX_CONTENT_LENGTH)
- Encrypted storage for sensitive documents
- OCR processing for document verification

For detailed email configuration instructions, see [`backend/EMAIL_CONFIG.md`](../backend/EMAIL_CONFIG.md).