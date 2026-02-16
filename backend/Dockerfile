FROM python:3.11-slim

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Create directories for outputs
RUN mkdir -p /app/uploads /app/clips /app/thumbnails /app/captions /app/voiceovers

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
