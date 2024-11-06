# Use the official Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy setup.py and install dependencies
COPY setup.py .
RUN pip install --no-cache-dir .

# Copy the FastAPI application code
COPY . .

# Expose the FastAPI port (default 8000)
EXPOSE 8000

# Environment variables for FastAPI
ENV HOST=0.0.0.0
ENV PORT=8000

# Run the FastAPI server with Uvicorn
CMD ["uvicorn", "app.main:setup", "--host", "0.0.0.0", "--port", "8000"]
