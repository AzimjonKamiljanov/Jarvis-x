FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    portaudio19-dev \
    libasound2-dev \
    espeak \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/
COPY README.md /app/
COPY . /app/

# Install the base package
RUN pip install --no-cache-dir -e .[voice,memory]

# Expose API port
EXPOSE 8000

# Run the API server by default
CMD ["python", "-m", "jarvis", "--api"]
