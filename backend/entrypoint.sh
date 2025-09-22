#!/bin/bash

# Ensure directories exist and have proper permissions
mkdir -p /usr/src/app/logs /usr/src/app/uploads

# Set proper permissions for current user (appuser)
chmod -R 755 /usr/src/app/logs /usr/src/app/uploads

# Execute the main command
exec "$@"
