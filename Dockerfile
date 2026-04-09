# Use Python slim image
FROM python:3.14-slim

# Install dependencies for headless Chrome
RUN apt-get update && apt-get install -y \
    wget unzip xvfb libnss3 libxss1 libasound2 \
    fonts-liberation libappindicator3-1 \
    libatk-bridge2.0-0 libgtk-3-0 libgbm1 \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y /tmp/chrome.deb \
    && rm /tmp/chrome.deb

# Install ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d'.' -f1) \
    && wget -q -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/$CHROME_VERSION/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && rm /tmp/chromedriver.zip

# Set environment variables
ENV PORT=10000

# Copy app files
WORKDIR /app
COPY requirements.txt .
COPY app.py .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run app
CMD ["python", "app.py"]