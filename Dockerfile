FROM python:3.12-slim

# System dependencies: Chromium for Selenium (agencijaZaVrabotuvanje) and Playwright deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
# Run Chromium in no-sandbox mode (required inside Docker)
ENV CHROMIUM_FLAGS="--no-sandbox --disable-dev-shm-usage"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright's Chromium browser (for uslugi, katastar, crm SSO auth)
RUN playwright install chromium --with-deps

COPY . .

# Default entrypoint: backend API server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
