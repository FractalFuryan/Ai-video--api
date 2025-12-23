# Dockerfile — HarmonyØ4 Production Image

FROM python:3.12-slim

LABEL maintainer="HarmonyØ4 Team"
LABEL description="HarmonyØ4 Media API — Deterministic transport layer"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml requirements.txt ./
COPY . ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Optional: binary compression core
# Mount core binary to /core if available
# Environment variable: HARMONY4_CORE_PATH=/core/libh4core.so
ENV HARMONY4_CORE_PATH=""

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run FastAPI server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
