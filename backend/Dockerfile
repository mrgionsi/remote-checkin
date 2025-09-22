# Use an official lightweight Python image
FROM python:3.13-slim

LABEL org.opencontainers.image.source="https://github.com/mrgionsi/remote-checkin"

# Set working directory
WORKDIR /usr/src/app

# Copy only required files (avoiding secrets)
COPY requirements.txt .

# Install system dependencies (only if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 tesseract-ocr && \
    rm -rf /var/lib/apt/lists/*


# Install Python dependencies
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Create necessary directories with proper permissions
RUN mkdir -p /usr/src/app/logs /usr/src/app/uploads

# Create a non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy application code while ignoring unnecessary files
COPY . .

# Copy and set up entrypoint script
COPY backend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set proper ownership and permissions
RUN chown -R appuser:appuser /usr/src/app && \
    chmod -R 755 /usr/src/app/logs && \
    chmod -R 755 /usr/src/app/uploads

# Switch to non-root user
USER appuser

# Set environment variables for Gunicorn
ENV GUNICORN_CMD_ARGS="--bind=0.0.0.0:8000 --chdir=/usr/src/app"

# Expose the Flask port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Run the application using Gunicorn
CMD ["gunicorn", "wsgi:app"]
