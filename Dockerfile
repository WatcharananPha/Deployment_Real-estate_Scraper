FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system packages commonly required for headless Chrome and builds
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    ca-certificates curl wget gnupg unzip build-essential git \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxcomposite1 libxrandr2 libgbm1 libgtk-3-0 fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy project
COPY . /app

# Create unprivileged user for running processes
RUN adduser --disabled-password --gecos '' appuser || true
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8888

# Default to an interactive shell so users can override CMD in compose/run
CMD ["/bin/bash"]