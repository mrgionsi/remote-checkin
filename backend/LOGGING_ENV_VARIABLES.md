# Logging Environment Variables

Add these environment variables to your `.env` file to configure the logging system.

## Required Environment Variables

```bash
# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

# Environment: development, production, or testing
# - development: Colored console output with detailed information + optional file logging
# - production: JSON structured logs with file rotation
# - testing: Minimal logging to avoid test noise
FLASK_ENV=development

# Enable debug mode (automatically sets FLASK_ENV to development if true)
DEBUG=true

# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
# - DEBUG: Very detailed information, typically of interest only when diagnosing problems
# - INFO: General information about what your application is doing
# - WARNING: Something unexpected happened, but the app is still working
# - ERROR: A serious problem occurred, but the app can continue
# - CRITICAL: A very serious error occurred, app may not be able to continue
LOG_LEVEL=INFO

# Enable/disable file logging (true/false)
# - true: Logs are written to files (recommended for production)
# - false: Logs only go to console
LOG_TO_FILE=true

# Directory for log files (relative to project root)
# Files created:
# - {LOG_DIRECTORY}/remote-checkin.log (all logs)
# - {LOG_DIRECTORY}/remote-checkin-error.log (errors only)
LOG_DIRECTORY=logs

# Maximum log file size in bytes before rotation
# Default: 10485760 (10MB)
# When file reaches this size, it's rotated to .log.1, .log.2, etc.
MAX_LOG_FILE_SIZE=10485760

# Number of backup log files to keep after rotation
# Default: 5 (keeps .log, .log.1, .log.2, .log.3, .log.4, .log.5)
LOG_BACKUP_COUNT=5

# Enable/disable SQLAlchemy query logging (true/false)
# - true: Shows all SQL queries in logs (useful for debugging)
# - false: Hides SQL queries (recommended for production)
# Note: This controls database.py echo parameter
DATABASE_ECHO=false
```

## Configuration Examples

### Development Setup (detailed logging)
```bash
FLASK_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG
LOG_TO_FILE=true
DATABASE_ECHO=true
```

### Production Setup (optimized logging)
```bash
FLASK_ENV=production
DEBUG=false
LOG_LEVEL=INFO
LOG_TO_FILE=true
DATABASE_ECHO=false
```

### Testing Setup (minimal logging)
```bash
FLASK_ENV=testing
DEBUG=false
LOG_LEVEL=WARNING
LOG_TO_FILE=false
DATABASE_ECHO=false
```

## How to Add to Your .env File

1. Open your `.env` file in the project root
2. Add the logging configuration section at the end
3. Adjust the values according to your needs
4. Restart the application to apply changes

## Environment Variable Details

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `production` | Environment mode (development/production/testing) |
| `DEBUG` | `false` | Enable debug mode (overrides FLASK_ENV if true) |
| `LOG_LEVEL` | `INFO` | Minimum log level to capture |
| `LOG_TO_FILE` | `true` | Write logs to files |
| `LOG_DIRECTORY` | `logs` | Directory for log files |
| `MAX_LOG_FILE_SIZE` | `10485760` | Max file size before rotation (10MB) |
| `LOG_BACKUP_COUNT` | `5` | Number of backup files to keep |
| `DATABASE_ECHO` | `false` | Show SQLAlchemy queries in logs |

## Log File Locations

When `LOG_TO_FILE=true`, logs are written to:

- **Main log**: `{LOG_DIRECTORY}/remote-checkin.log` - All logs
- **Error log**: `{LOG_DIRECTORY}/remote-checkin-error.log` - Errors only
- **Rotated logs**: `{LOG_DIRECTORY}/remote-checkin.log.1`, `.log.2`, etc.

## Log Formats

### Development Format (Colored Console)
```
[INFO    ] 2024-01-15 10:30:45 [a1b2c3d4] routes.room_routes:add_room:98 - Room created successfully
```

### Production Format (JSON)
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "routes.room_routes",
  "message": "Room created successfully",
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "extra": {
    "room_id": 123,
    "room_name": "Deluxe Suite"
  }
}
```
