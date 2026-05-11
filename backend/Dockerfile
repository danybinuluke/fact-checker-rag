# ══════════════════════════════════════════════════════════════════
# Fact-Checking RAG System — Dockerfile
# ══════════════════════════════════════════════════════════════════
# Multi-stage build for Railway.app deployment
# ══════════════════════════════════════════════════════════════════

FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Copy application code
COPY . .

# Expose port (Railway sets PORT env var)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# Run with uvicorn
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
