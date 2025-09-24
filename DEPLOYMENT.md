# Docker Compose Deployment Guide

## Overview

This guide provides instructions for deploying the Remote Check-in application using Docker Compose with proper volume configuration for data persistence.

## Volume Configuration

### Required Volumes

The application requires the following persistent volumes:

#### 1. **Database Volume** (`postgres_data`)

- **Purpose**: PostgreSQL database data persistence
- **Mount Point**: `/var/lib/postgresql/data`
- **Critical**: Contains all application data (users, reservations, clients)

#### 2. **Uploads Volume** (`uploads_data`)

- **Purpose**: User-uploaded identity documents and images
- **Mount Point**: `/usr/src/app/uploads`
- **Contents**:
  - Identity document images (front/back/selfie)
  - Organized by reservation ID folders
  - Critical for document verification

#### 3. **Logs Volume** (`logs_data`)

- **Purpose**: Application logs with rotation
- **Mount Point**: `/usr/src/app/logs`
- **Contents**:
  - `remote-checkin.log` - Application logs
  - `remote-checkin-error.log` - Error logs
  - Rotated log files with backup retention

### Volume Benefits

- **Data Persistence**: All data survives container restarts and updates
- **Backup Ready**: Volumes can be easily backed up independently
- **Scalability**: Volumes can be moved to external storage systems
- **Security**: Sensitive data (uploads) isolated from application code

## Environment Variables

Create a `.env` file with the following variables:

```bash
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

## Deployment Commands

### 1. Initial Deployment

```bash
# Build and start all services
docker-compose up -d --build

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### 2. Backup Data

```bash
# Backup database
docker-compose exec postgres pg_dump -U remotecheckin remotecheckin > backup.sql

# Backup uploads
docker run --rm -v remote-checkin_uploads_data:/data -v $(pwd):/backup alpine tar czf /backup/uploads-backup.tar.gz -C /data .

# Backup logs
docker run --rm -v remote-checkin_logs_data:/data -v $(pwd):/backup alpine tar czf /backup/logs-backup.tar.gz -C /data .
```

### 3. Restore Data

```bash
# Restore database
docker-compose exec -T postgres psql -U remotecheckin remotecheckin < backup.sql

# Restore uploads
docker run --rm -v remote-checkin_uploads_data:/data -v $(pwd):/backup alpine tar xzf /backup/uploads-backup.tar.gz -C /data

# Restore logs
docker run --rm -v remote-checkin_logs_data:/data -v $(pwd):/backup alpine tar xzf /backup/logs-backup.tar.gz -C /data
```

### 4. Maintenance Commands

```bash
# Update application
docker-compose pull
docker-compose up -d --build

# Scale backend (if needed)
docker-compose up -d --scale backend=3

# View volume usage
docker system df -v

# Clean up unused volumes
docker volume prune
```

## Security Considerations

### Volume Security

- **Uploads**: Contains sensitive identity documents
- **Logs**: May contain PII (automatically filtered)
- **Database**: Contains all user data

### Access Control

- Use non-root users in containers
- Restrict volume access permissions
- Encrypt sensitive volumes if required
- Regular security updates for base images

## Monitoring

### Health Checks

All services include health checks:

- **PostgreSQL**: `pg_isready` command
- **Backend**: HTTP health endpoint
- **Frontend**: HTTP availability check

### Log Monitoring

```bash
# Follow application logs
docker-compose logs -f backend

# Check error logs
docker-compose exec backend tail -f /usr/src/app/logs/remote-checkin-error.log

# Monitor volume usage
docker system df
```

## Troubleshooting

### Common Issues

1. **Volume Permission Errors**

   ```bash
   # Fix permissions
   docker-compose exec backend chown -R appuser:appuser /usr/src/app/uploads
   ```

2. **Database Connection Issues**

   ```bash
   # Check database health
   docker-compose exec postgres pg_isready -U remotecheckin
   ```

3. **Upload Issues**
   ```bash
   # Check upload directory
   docker-compose exec backend ls -la /usr/src/app/uploads
   ```

### Performance Optimization

1. **Volume Performance**

   - Use local SSD storage for better I/O
   - Consider network-attached storage for high availability

2. **Log Rotation**

   - Adjust `MAX_LOG_FILE_SIZE` and `LOG_BACKUP_COUNT`
   - Monitor disk usage regularly

3. **Database Optimization**
   - Regular VACUUM and ANALYZE operations
   - Monitor query performance

## Production Recommendations

1. **External Volumes**: Use external volume drivers for production
2. **Backup Strategy**: Implement automated backup procedures
3. **Monitoring**: Set up log aggregation and monitoring
4. **Security**: Regular security updates and vulnerability scans
5. **SSL/TLS**: Use reverse proxy with SSL termination
6. **Resource Limits**: Set appropriate memory and CPU limits

## Support

For deployment issues or questions, refer to:

- Application logs in `/usr/src/app/logs`
- Docker Compose logs: `docker-compose logs`
- Volume inspection: `docker volume inspect <volume_name>`
