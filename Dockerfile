# Multi-stage build for Hugging Face Spaces
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt .

# Install Python dependencies with memory optimization
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Create necessary directories
RUN mkdir -p /app/backend/exports/charts /app/backend/data

# Expose port
EXPOSE 7860

# Set environment variables for production
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

# Hugging Face Spaces uses port 7860 by default
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "7860"]
