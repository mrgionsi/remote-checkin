# 📲 Remote Check-in <span align="left">

Remote check-in is a self-hosted solution designed to handle the check-in process for Bed and Breakfasts (B&Bs) remotely. This system allows you to manage your properties and rooms, create reservations, and collect necessary guest information, documents, and photos before arrival.

<p>
 <a href="https://github.com/mrgionsi/remote-checkin/releases"><img alt="GitHub Release" src="https://img.shields.io/github/v/release/mrgionsi/remote-checkin" hspace="6px" vspace="2px"></a>
 <a href="https://github.com/mrgionsi/remote-checkin/releases"><img alt="Project Build Workflow" src="https://img.shields.io/github/actions/workflow/status/mrgionsi/remote-checkin/build.yml" vspace="2px"></a>
 <a href="https://github.com/mrgionsi/remote-checkin/issues"><img alt="GitHub Issues" src="https://img.shields.io/github/issues/mrgionsi/remote-checkin" hspace="6px" vspace="2px"></a>
</p>

## ⚡️ Key Features & Benefits

* **Remote Check-in:** Guests can complete their check-in process remotely, saving time and streamlining operations.
* **Structure Management:** Easily manage your B&B locations, rooms, and associated details.
* **Reservation Management:** Create, update, and track reservations efficiently.
* **Information Collection:** Securely collect mandatory guest information, including documents and self-portraits.
* **Self-Hosted:** Maintain complete control over your data and system.
* **Customizable:** Flexible configuration options to tailor the system to your specific needs.

## 🚀 Deployment

Follow this chapter to get the Remote Check-In app up and running in your environment.

### Prerequisites & Dependencies

Before installing and setting up Remote Check-in, ensure you have the following tools and dependencies:

* **Python:** Version 3.7 or higher
* **Node.js:** Latest LTS version
* **Docker:** Docker Engine installed and running
  * **Docker Compose** is optional, but recommended 
* **Database:** PostgreSQL or similar (configure through environment variables)
* **SMTP Server:** For email functionality (e.g., Gmail, Sendgrid)

### Installation & Setup Instructions

Follow these steps to install and set up Remote Check-in:

1.  **Clone the Repository:**

    ```bash
    git clone https://github.com/mrgionsi/remote-checkin.git
    cd remote-checkin
    ```

2.  **Configure Environment Variables:**

    Create a `.env` file in the root directory and populate it with the necessary environment variables:

    ```
    DB_HOST=<your_database_host>
    DB_PORT=<your_database_port>
    DB_USER=<your_database_username>
    DB_PASSWORD=<your_database_password>
    DB_NAME=<your_database_name>
    DATABASE_TYPE=<your_database_type> # e.g., postgresql

    MAIL_SERVER=<your_mail_server>
    MAIL_PORT=<your_mail_port>
    MAIL_USERNAME=<your_mail_username>
    MAIL_PASSWORD=<your_mail_password>
    MAIL_DEFAULT_SENDER=<your_default_sender_email>

    # Other necessary environment variables...
    ```
    Refer to `backend/EMAIL_CONFIG.md` and other configuration files for a comprehensive list of required variables.

3. **Install the project dependencies:**

    ```bash
    # Backend Python dependencies
    $ pip install -r backend/requirements.txt
    # Frontend Node.js dependencies
    $ cd frontend && npm install
    ```

4.  **Build and Run with Docker Compose (Recommended):**

    ```bash
    docker-compose up --build
    ```

5. **Alternative Run using Docker**
    ```bash
    # Build the docker image
    docker build -t remote-checkin-backend backend/
    # Run the docker image
    docker run -p 8000:8000 remote-checkin-backend
    ```

    This command builds the Docker images and starts the application containers. Access the application through your web browser.  Refer to the Dockerfile for port configurations.

6.  **Manual Setup (without Docker):**

    a. Configure the database connection in `backend/config.py` (or through environment variables).

    b. Run the backend application: `python main.py`.

    c. Run the frontend application

## 📄 Usage Examples & API Documentation

Detailed API documentation and usage examples will be available at [Documentation](https://tbd) once finalized. This documentation will cover:

* API endpoints for managing structures, rooms, and reservations.
* Data models and schemas.
* Authentication and authorization procedures.
* Sample code snippets for common use cases.

## 📝 Configuration Options

The Remote Check-in system offers various configuration options, including:

* **Database Configuration:** Specify database connection details (IP, port, username, password, database name, type) via environment variables. Supported database types include PostgreSQL, MySQL, and SQLite.
* **Email Configuration:** Configure SMTP server settings (server, port, username, password, sender address) for sending email notifications. Refer to `backend/EMAIL_CONFIG.md` for detailed instructions and environment variables.
* **Application Settings:** Customize application-specific settings (e.g., image storage location, allowed file types) through environment variables or configuration files.

## 👥 Contributing Guidelines

We welcome contributions to the Remote Check-in project! To contribute, please follow these guidelines:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Implement your changes, adhering to coding standards.
4. Write clear and concise commit messages.
5. Submit a pull request with a detailed description of your changes.

## 📜 License Information

This project is licensed under the [GNU Affero General Public License v3.0](https://www.gnu.org/licenses/agpl-3.0.en.html). See the `LICENSE` file for more information.

## Acknowledgments

* This project utilizes various open-source libraries and frameworks, including Python, TypeScript, and [list any other significant libraries].
* We thank the open-source community for their contributions to these essential tools.
