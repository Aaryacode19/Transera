# Use lightweight Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install OS dependencies
RUN apt-get update && apt-get install -y \
    libgl1 libglib2.0-0 ffmpeg tesseract-ocr \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Copy files
COPY requirements.txt ./
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port for Flask
EXPOSE 5000

# Run the bot
CMD ["python", "Transera.py"]
