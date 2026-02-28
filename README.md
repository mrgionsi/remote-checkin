# 🪪 Remote Check-in

Remote Check-in solution is self-hosted and designed to handle check-ins for a bed and breakfast remotely. 

After setting up your B&B and its rooms, you can add a reservation and ask clients to fill in required information and upload documents and selfies.  

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

- OS: macOS, Linux, or Windows (WSL2 recommended on Windows)
- Python: 3.11+ (tested with 3.13)
- Node.js: 20 LTS+ (Angular 19 project)
- npm: 10+
- PostgreSQL: 14+
- OCR runtime: Tesseract OCR 5+ available on `PATH`
- Docker / Podman (optional, but recommended for local PostgreSQL)
- Java: not required

### Installing

Follow the steps below to setup the development environment:

1. Clone the repository and move into it:

```bash
git clone https://github.com/mrgionsi/remote-checkin.git
cd remote-checkin
```

2. Create your local environment file in the repository root:

```bash
cp .env.example .env 2>/dev/null || touch .env
```

3. Add the required variables to `.env`:

| Variable | Required | Example | Description |
| --- | --- | --- | --- |
| `DB_USER` | Yes | `remotecheckin` | PostgreSQL user for backend connection |
| `DB_PASSWORD` | Yes | `change_me` | PostgreSQL password |
| `DB_HOST` | Yes | `127.0.0.1` | PostgreSQL host |
| `DB_PORT` | Yes | `5432` | PostgreSQL port |
| `DB_NAME` | Yes | `remotecheckin` | PostgreSQL database name |
| `JWT_SECRET_KEY` | Yes | `a_very_long_random_secret_123!` | JWT signing key (min 16 chars, letters + number/symbol) |
| `ALLOWED_CORS` | No | `http://localhost:4200,http://127.0.0.1:4200` | Comma-separated frontend origins |
| `DEBUG` | No | `true` | Enables Flask debug mode |
| `FLASK_ENV` | No | `development` | App/logging environment |
| `DATABASE_ECHO` | No | `false` | SQLAlchemy SQL logging |
| `MAIL_MAX_EMAILS` | No | `100` | Mail batch limit |
| `MAIL_ASCII_ATTACHMENTS` | No | `false` | Flask-Mail attachment mode |
| `PII_HASH_SALT` | No | `replace_with_random_salt` | Salt for PII hashing in logs |
| `LOG_LEVEL` | No | `INFO` | Log verbosity |
| `LOG_TO_FILE` | No | `true` | Enable file logging |
| `LOG_DIRECTORY` | No | `logs` | Folder for log files |
| `MAX_LOG_FILE_SIZE` | No | `10485760` | Max log file size in bytes |
| `LOG_BACKUP_COUNT` | No | `5` | Rotated log files to keep |

4. Start PostgreSQL and initialize schema.

Option A (recommended with Docker):

```bash
docker compose -f docker-compose-dev.yaml up -d postgres
```

Option B (local PostgreSQL):

```bash
createdb remotecheckin
psql -d remotecheckin -f database/init.sql
```

5. Install backend dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

6. Install frontend dependencies:

```bash
cd frontend
npm install
cd ..
```

7. Run the app in development (two terminals):

Backend:

```bash
source .venv/bin/activate
cd backend
python main.py
```

Frontend:

```bash
cd frontend
npm start
```

8. Run tests:

Backend:

```bash
PYTHONPATH=backend pytest backend/tests -q
```

Frontend unit tests:

```bash
cd frontend
npm run test:ci
```

Optional frontend smoke E2E:

```bash
cd frontend
npm run e2e:smoke
```

Quick start from a fresh checkout:

```bash
docker compose -f docker-compose-dev.yaml up -d postgres && \
python3 -m venv .venv && source .venv/bin/activate && \
pip install -r backend/requirements.txt && \
cd frontend && npm install && npm start
```

## Deployment

Using containers makes the `remote-checkin` installation easy.

1. Create an `.env` file with the following variables:

```dotenv
# Database Configuration
DB_USER=remotecheckin
DB_PASSWORD=your_secure_password_here
DB_NAME=remotecheckin
DB_HOST=postgres
DB_PORT=5432

# Application Configuration
FLASK_ENV=production
BACKEND_PORT=8000
FRONTEND_PORT=80

# JWT Configuration
JWT_SECRET_KEY=your_jwt_secret_key_here

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_USE_TLS=true
MAIL_USE_SSL=false

# Logging Configuration
LOG_TO_FILE=true
LOG_LEVEL=INFO
LOG_DIRECTORY=logs
MAX_LOG_FILE_SIZE=10485760
LOG_BACKUP_COUNT=5

# PII Protection
PII_HASH_SALT=your_pii_hash_salt_here
```

2. Use the following [`docker-compose.yaml`](docker-compose.yaml) to spin up a `remote-checkin` instance:

```shell
docker compose up -d
```

The application will be available at [http://localhost:80](http://localhost:80).

You can fetch both the backend and frontend Container Images from the [GitHub Container Registry](https://github.com/mrgionsi?tab=packages&repo_name=remote-checkin).

## Built With

* [PostgreSQL](https://www.postgresql.org/)
* [Flask](https://flask.palletsprojects.com/en/stable/)
* [Angular](https://angular.dev/)

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](https://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/mrgionsi/remote-checkin/tags). 

## Authors

* **Giovanni Pasquariello** - *Initial work* - [mrgionsi](https://github.com/mrgionsi)

See also the list of [contributors](https://github.com/mrgionsi/remote-checkin/contributors) who participated in this project.

## License

This project is licensed under the AGPL-3.0 license - see the [LICENSE](LICENSE) file for details.

<!-- ## Acknowledgments

* Hat tip to anyone whose code was used
* Inspiration
* etc -->
