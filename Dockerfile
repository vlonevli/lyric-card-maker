FROM python:3.11-slim

# Install essential system dependencies for Pillow image rendering and font handling
RUN apt-get update && apt-get install -y --no-install-recommends \
    fontconfig \
    libfreetype6-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files and assets
COPY . .

# Expose port
EXPOSE 10000

# Run the bot
CMD ["python", "bot.py"]
