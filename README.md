
# Remote Check-in

Remote check-in is a self-hosted to handle the check-in for a B&B remotely. 

Setting up your structures (B&Bs) and relative rooms, you can add a reservation and ask clients to fill in mandatory informations and upload documents and selfie. 

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

- Python
- Docker / Podman
- NodeJs

### Installing

Follow the steps below to setup the development environment:

- 🚧 W.I.P.

## Deployment

Using containers makes the `remote-checkin` installation easy.

1. Create an `.env` file with the following variables:

```
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
$ docker-compose up -d
```

The application will be available at [localhost:80](localhost:80).

You can fetch both the backend and frontend Container Images from the [GitHub Container Registry](https://github.com/mrgionsi?tab=packages&repo_name=remote-checkin).

## Built With

* [PostgreSQL](https://www.postgresql.org/)
* [Flask](https://flask.palletsprojects.com/en/stable/)
* [Angular](https://angular.dev/)

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/mrgionsi/remote-checkin/tags). 

## Authors

* **Giovanni Pasquariello** - *Initial work* - [mrgionsi](https://github.com/mrgionsi)

See also the list of [contributors](https://github.com/mrgionsi/remote-checkin/contributors) who participated in this project.

## License

This project is licensed under the AGPL-3.0 license - see the [LICENSE](LICENSE) file for details.

<!-- ## Acknowledgments

* Hat tip to anyone whose code was used
* Inspiration
* etc -->
