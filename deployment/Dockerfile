# Base image: Python 3.11 slim for minimal size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for Chrome, Selenium, and web scraping
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libgcc1 \
    libgconf-2-4 \
    libgdk-pixbuf1.0-0 \
    libglib2.0-0 \
    libgtk-3-0 \
    libharfbuzz0b \
    libice6 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpci3 \
    libpixman-1-0 \
    libsm6 \
    libstdc++6 \
    libx11-6 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxinerama1 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    lsb-release \
    wget \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project into container
COPY . .

# Create data directory and chrome-profile directory for persistence
RUN mkdir -p /app/data /app/chrome-profile

# Expose Jupyter Lab port
EXPOSE 8888

# Default command: Start Jupyter Lab (can be overridden for running scrapers)
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", "--NotebookApp.token=", "--NotebookApp.password="]
