# 📲 Remote Check-in

Remote Check-in is a comprehensive self-hosted solution designed to handle the check-in process for Bed and Breakfasts (B&Bs) and hotels remotely. This system allows property owners to manage their properties and rooms, create reservations, and securely collect necessary guest information, documents, and photos before arrival.

## 🏗️ Technology Stack

- **Backend**: Flask (Python) with SQLAlchemy ORM
- **Frontend**: Angular 19 with PrimeNG UI components
- **Database**: PostgreSQL
- **Authentication**: JWT-based authentication
- **Email**: Flask-Mail with SMTP support
- **File Storage**: Local file system with encrypted uploads
- **Internationalization**: Multi-language support (EN, ES, IT, FR, DE)
- **Deployment**: Docker & Docker Compose ready

<p>
 <a href="https://github.com/mrgionsi/remote-checkin/releases"><img alt="GitHub Release" src="https://img.shields.io/github/v/release/mrgionsi/remote-checkin" hspace="6px" vspace="2px"></a>
 <a href="https://github.com/mrgionsi/remote-checkin/releases"><img alt="Project Build Workflow" src="https://img.shields.io/github/actions/workflow/status/mrgionsi/remote-checkin/build.yml" vspace="2px"></a>
 <a href="https://github.com/mrgionsi/remote-checkin/issues"><img alt="GitHub Issues" src="https://img.shields.io/github/issues/mrgionsi/remote-checkin" hspace="6px" vspace="2px"></a>
</p>

## ⚡️ Key Features & Benefits

### For Property Owners

- **Admin Dashboard**: Comprehensive dashboard with reservation analytics and charts
- **Structure & Room Management**: Easily manage multiple B&B locations and rooms
- **Reservation Management**: Create, update, and track reservations with detailed client information
- **Multi-User Support**: Role-based access control with admin and superadmin roles
- **Email Integration**: Automated email notifications and confirmations
- **Settings Management**: Configure email providers and system settings

### For Guests

- **Remote Check-in Process**: Complete check-in remotely before arrival
- **Multi-language Support**: Available in English, Spanish, Italian, French, and German
- **Document Upload**: Secure upload of identity documents (front, back, selfie)
- **Mobile-Friendly**: Responsive design works on all devices
- **Reservation Lookup**: Easy reservation verification with unique codes

### Security & Compliance

- **Data Encryption**: Secure file storage with encryption
- **JWT Authentication**: Industry-standard authentication
- **Document Validation**: OCR processing for document verification
- **Self-Hosted**: Complete control over your data and privacy

## 🚀 Deployment

Follow this chapter to get the Remote Check-In app up and running in your environment.

### Prerequisites & Dependencies

Before installing and setting up Remote Check-in, ensure you have the following tools and dependencies:

- **Python:** Version 3.7 or higher
- **Node.js:** Version 18+ (Latest LTS version recommended)
- **Docker:** Docker Engine installed and running
- **Docker Compose:** Version 3.8+ (recommended for development)
- **PostgreSQL:** Version 12+ (can be run via Docker)
- **SMTP Server:** For email functionality (Gmail, Sendgrid, or any SMTP provider)

### Installation & Setup Instructions

Follow these steps to install and set up Remote Check-in:

1.  **Clone the Repository:**

    ```bash
    git clone https://github.com/mrgionsi/remote-checkin.git
    cd remote-checkin
    ```

2.  **Configure Environment Variables:**

    Create a `.env` file in the root directory and populate it with the necessary environment variables:

    ```env
    # Database Configuration
    DB_HOST=localhost
    DB_PORT=5432
    DB_USER=your_db_user
    DB_PASSWORD=your_db_password
    DB_NAME=remotecheckin
    DATABASE_TYPE=postgresql

    # JWT Configuration (REQUIRED - Generate a strong secret key)
    JWT_SECRET_KEY=your_very_strong_jwt_secret_key_here_minimum_16_chars

    # Email Configuration
    MAIL_SERVER=smtp.gmail.com
    MAIL_PORT=587
    MAIL_USE_TLS=True
    MAIL_USERNAME=your_email@gmail.com
    MAIL_PASSWORD=your_app_password
    MAIL_DEFAULT_SENDER_EMAIL=your_email@gmail.com
    MAIL_DEFAULT_SENDER_NAME=Remote Check-in System
    EMAIL_ENCRYPTION_KEY=your_generated_email_encryption_key_here

    # CORS Configuration
    ALLOWED_CORS=http://localhost:4200

    # File Upload Configuration
    UPLOAD_FOLDER=uploads
    MAX_CONTENT_LENGTH=16777216  # 16MB max file size
    ```

    **Important**:

    - Generate a strong JWT secret key (minimum 16 characters with letters and numbers/symbols)
    - For Gmail, enable 2FA and use an App Password (see `backend/EMAIL_CONFIG.md`)
    - Generate an encryption key for email passwords: `python backend/generate_encryption_key.py`
    - Refer to `backend/EMAIL_CONFIG.md` for detailed email configuration instructions

3.  **Start Database with Docker Compose (Recommended):**

    ```bash
    # Start PostgreSQL database
    docker-compose -f docker-compose-dev.yaml up -d postgres
    ```

4.  **Build and Run the Application:**

    **Option A: Full Docker Setup (Recommended for Production)**

    ```bash
    # Build and run both frontend and backend
    docker-compose up --build
    ```

    **Option B: Development Setup (Backend with Docker, Frontend locally)**

    ```bash
    # Start database
    docker-compose -f docker-compose-dev.yaml up -d postgres

    # Install backend dependencies
    pip install -r backend/requirements.txt

    # Run backend (will be available at http://localhost:8000)
    cd backend && python main.py

    # In another terminal, install and run frontend
    cd frontend && npm install && npm start
    # Frontend will be available at http://localhost:4200
    ```

5.  **Access the Application:**
    - **Frontend**: http://localhost:4200 (Angular app)
    - **Backend API**: http://localhost:5000 (Flask API)
    - **Admin Panel**: http://localhost:4200/admin (Login required)

## 📄 API Documentation

The Remote Check-in system provides a comprehensive REST API built with Flask. All endpoints are prefixed with `/api/v1/` and require JWT authentication for admin operations.

### Authentication Endpoints

| Method | Endpoint                    | Description                             |
| ------ | --------------------------- | --------------------------------------- |
| `POST` | `/api/v1/admin/login`       | Admin user authentication               |
| `POST` | `/api/v1/admin/create-user` | Create new admin user (superadmin only) |
| `GET`  | `/api/v1/admin/profile`     | Get current user profile                |

### Room Management

| Method   | Endpoint             | Description                    |
| -------- | -------------------- | ------------------------------ |
| `GET`    | `/api/v1/rooms`      | List all rooms for a structure |
| `POST`   | `/api/v1/rooms`      | Create a new room              |
| `GET`    | `/api/v1/rooms/<id>` | Get room details               |
| `PUT`    | `/api/v1/rooms/<id>` | Update room information        |
| `DELETE` | `/api/v1/rooms/<id>` | Delete a room                  |

### Reservation Management

| Method | Endpoint                                        | Description                        |
| ------ | ----------------------------------------------- | ---------------------------------- |
| `GET`  | `/api/v1/reservations`                          | List all reservations              |
| `GET`  | `/api/v1/reservations/<structure_id>`           | Get reservations by structure      |
| `GET`  | `/api/v1/reservations/monthly/<structure_id>`   | Get monthly reservation statistics |
| `POST` | `/api/v1/reservations`                          | Create a new reservation           |
| `GET`  | `/api/v1/reservations/<reservation_id>/clients` | Get clients for a reservation      |

### Client Check-in Process

| Method | Endpoint                                     | Description                                   |
| ------ | -------------------------------------------- | --------------------------------------------- |
| `POST` | `/api/v1/reservations/<id>/client-images`    | Check client image upload status              |
| `GET`  | `/api/v1/images/<reservation_id>/<filename>` | Serve client identity images                  |
| `POST` | `/api/v1/upload-reservation`                 | Upload client documents and complete check-in |

### Email Configuration

| Method | Endpoint                       | Description                |
| ------ | ------------------------------ | -------------------------- |
| `GET`  | `/api/v1/email-config`         | Get email configuration    |
| `POST` | `/api/v1/email-config`         | Update email settings      |
| `GET`  | `/api/v1/email-config/test`    | Test email configuration   |
| `GET`  | `/api/v1/email-config/presets` | Get email provider presets |

### Authentication

All admin endpoints require a valid JWT token in the Authorization header:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8000/api/v1/rooms
```

### Sample API Usage

**Create a new reservation:**

```bash
curl -X POST http://localhost:8000/api/v1/reservations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "reference_id": "RES-001",
    "start_date": "2024-01-15",
    "end_date": "2024-01-17",
    "room_id": 1,
    "clients": [
      {
        "name": "John",
        "surname": "Doe",
        "document_type": "passport",
        "document_number": "AB123456"
      }
    ]
  }'
```

## 📝 Configuration Options

The Remote Check-in system offers extensive configuration options through environment variables:

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

For detailed email configuration instructions, see [`backend/EMAIL_CONFIG.md`](backend/EMAIL_CONFIG.md).

## 🖥️ User Interface

The Remote Check-in system features a modern, responsive web interface built with Angular and PrimeNG components:

### Guest Interface

- **Language Selection**: Choose from 5 supported languages (EN, ES, IT, FR, DE)
- **Reservation Lookup**: Enter reservation code to access check-in process
- **Remote Check-in Form**: Multi-step form for guest information and document upload
- **Document Upload**: Secure upload of identity documents (front, back, selfie)
- **Mobile-Responsive**: Optimized for mobile devices and tablets

### Admin Interface

- **Dashboard**: Overview with reservation statistics and charts
- **Room Management**: Add, edit, and manage rooms and structures
- **Reservation Management**: Create and manage reservations with client details
- **Settings**: Configure email providers and system settings
- **User Management**: Manage admin users and permissions
- **Reservation Details**: View detailed reservation information and client documents

### Key UI Features

- **PrimeNG Components**: Professional UI components with consistent styling
- **Internationalization**: Full multi-language support with Transloco
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Dark/Light Themes**: Configurable theme support
- **Toast Notifications**: User-friendly feedback messages
- **Form Validation**: Real-time form validation with error messages

## 📁 Project Structure

```
remote-checkin/
├── backend/                 # Flask backend application
│   ├── routes/             # API route definitions
│   ├── models.py           # Database models
│   ├── config.py           # Configuration settings
│   ├── email_handler.py    # Email service
│   └── utils/              # Utility functions
├── frontend/               # Angular frontend application
│   ├── src/app/           # Angular components and services
│   ├── src/assets/        # Static assets and translations
│   └── src/environments/  # Environment configurations
├── database/              # Database initialization scripts
└── docker-compose-dev.yaml # Development Docker configuration
```

## 👥 Contributing Guidelines

We welcome contributions to the Remote Check-in project! To contribute, please follow these guidelines:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Implement your changes, adhering to coding standards.
4. Write clear and concise commit messages.
5. Submit a pull request with a detailed description of your changes.

## 📜 License Information

This project is licensed under the [GNU Affero General Public License v3.0](https://www.gnu.org/licenses/agpl-3.0.en.html). See the `LICENSE` file for more information.

## 📚 Additional Documentation

- **[Email Configuration Guide](backend/EMAIL_CONFIG.md)**: Detailed instructions for setting up email functionality
- **[Google OAuth Setup](GOOGLE_OAUTH_README.md)**: Instructions for Google authentication integration
- **[Portal Integration](PORTALE_ALLOGGI_INTEGRATION.md)**: Integration with external booking portals
- **[SOAP API Documentation](SOAP_API_DOCUMENTATION.md)**: SOAP API integration documentation

## 🛠️ Development

### Running Tests

```bash
# Backend tests
cd backend && python -m pytest tests/

# Frontend tests
cd frontend && npm test
```

### Code Quality

The project uses several tools to maintain code quality:

- **Backend**: pylint, black, isort for Python code formatting
- **Frontend**: ESLint, Prettier for TypeScript code formatting
- **Pre-commit hooks**: Automated code quality checks

## 🐛 Troubleshooting

### Common Issues

1. **JWT Secret Key Error**: Ensure your JWT_SECRET_KEY is at least 16 characters long and contains both letters and numbers/symbols.

2. **Database Connection Issues**: Verify your database credentials and ensure PostgreSQL is running.

3. **Email Configuration**: For Gmail, ensure 2FA is enabled and you're using an App Password.

4. **CORS Errors**: Check your ALLOWED_CORS environment variable includes your frontend URL.

5. **File Upload Issues**: Ensure the uploads directory exists and has proper write permissions.

## 📞 Support

If you encounter issues or need help:

1. Check the [Issues](https://github.com/mrgionsi/remote-checkin/issues) page for existing solutions
2. Create a new issue with detailed information about your problem
3. Include your environment details and error logs

## Acknowledgments

- This project utilizes various open-source libraries and frameworks, including Flask, Angular, PrimeNG, PostgreSQL, and many others.
- We thank the open-source community for their contributions to these essential tools and frameworks.
- Special thanks to the PrimeNG team for the excellent UI component library.
