FROM python:3.13-slim

# Install FFmpeg for voice support
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install uv for faster dependency resolution
RUN pip install --no-cache-dir uv

# Install dependencies
RUN uv pip install --system --no-cache -e .

# Copy application code
COPY src/ ./src/
COPY assets/ ./assets/

# Create data directory for database
RUN mkdir -p /app/data

# Set Python path
ENV PYTHONPATH=/app/src

# Run bot
CMD ["python", "-m", "athan.bot"]

