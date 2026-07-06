# Use a lightweight official Python base image
FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Prevent Python from writing .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy directories
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY data/ ./data/

# Expose port
EXPOSE 2026

# Command to run uvicorn server
CMD ["python", "backend/server.py"]
