# Start with a base Python image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy necessary files for installation
COPY setup.py .
COPY README.md .
COPY requirements.txt .

# Install git to allow installation of dependencies from GitHub
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Expose the port the application will run on
EXPOSE 8000

# Specify the command to run the application
CMD ["python", "-m", "superpilot"]
