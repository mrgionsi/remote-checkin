# Use an official lightweight Python image
FROM python:3.13-slim

LABEL org.opencontainers.image.source="https://github.com/mrgionsi/remote-checkin"

# Set working directory
WORKDIR /usr/src/app

# Copy only required files (avoiding secrets)
COPY requirements.txt .

# Install system dependencies (only if needed)
RUN apt-get update && apt-get install -y libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

# Install tesseract
RUN apt install tesseract-ocr

# Install Python dependencies
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Create a non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy application code while ignoring unnecessary files
COPY . .
RUN chown -R appuser:appuser /usr/src/app

# Switch to non-root user
USER appuser

# Set environment variables for Gunicorn
ENV GUNICORN_CMD_ARGS="--bind=0.0.0.0:8000 --chdir=/usr/src/app"

# Expose the Flask port
EXPOSE 8000

# Run the application using Gunicorn
CMD ["gunicorn", "wsgi:app"]
