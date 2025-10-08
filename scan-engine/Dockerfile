# Use the official OWASP ZAP stable image as the base
FROM owasp/zap2docker-stable:latest

# Set the working directory
WORKDIR /zap

# The ZAP user is 'zap'. Switch to the root user to install packages.
USER root

# Install Python, pip, and other necessary tools
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Copy the Python requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the scanner worker script into the container
COPY scanner_worker.py .

# Switch back to the 'zap' user for security
USER zap

# Entrypoint will be set at runtime to start ZAP and then run the script
