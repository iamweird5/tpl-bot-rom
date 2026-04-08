FROM python:3.11-slim

# Install Chrome + dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    chromium \
    chromium-driver \
    fonts-liberation \
    libnss3 \
    libxss1 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libgtk-3-0 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables for Chrome
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Set working directory
WORKDIR /app

# Copy files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Start app
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]