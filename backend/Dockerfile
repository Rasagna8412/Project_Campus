# ==============================================================================
# Project Campus — Production & Integration Backend Container
# Python 3.12 Slim Multi-Stage Build
# ==============================================================================

# --- Stage 1: Build Dependencies ---
FROM python:3.12-slim AS builder

WORKDIR /build

# Install compilation prerequisites
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements specification
COPY requirements.txt .

# Install dependencies into isolated virtual environment
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# --- Stage 2: Runtime Container ---
FROM python:3.12-slim AS runner

WORKDIR /app

# Install runtime utilities for container health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Create non-root system user and group for runtime security
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Copy application code and Alembic migrations with non-root ownership
COPY --chown=appuser:appgroup app /app/app
COPY --chown=appuser:appgroup alembic /app/alembic
COPY --chown=appuser:appgroup alembic.ini /app/alembic.ini
COPY --chown=appuser:appgroup scripts /app/scripts

# Switch to non-root runtime user
USER appuser

# Container health check querying FastAPI /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Controlled ASGI startup command
# NOTE: Database migrations must be run explicitly (e.g. `alembic upgrade head`)
# and are not executed inside worker startup to prevent migration race conditions.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
