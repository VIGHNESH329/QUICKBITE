# ==============================================================================
# QuickBite Secure Multi-Stage / Minimal Production Dockerfile
# Security Controls:
# - Minimal base image (python:3.11-slim)
# - Dedicated non-privileged user (appuser:10001)
# - No secrets embedded in image
# - Version-pinned dependencies
# - Exposed only on port 8000
# ==============================================================================

FROM python:3.11-slim AS runtime

# Set security and performance environment flags
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    APP_HOME=/home/appuser/quickbite \
    PYTHONPATH=/home/appuser/quickbite/backend

# Install security updates and curl for container health checks
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Create dedicated non-root user and group (UID 10001)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -m -s /bin/bash appuser

WORKDIR ${APP_HOME}

# Copy and install pinned requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create dedicated persistent data directory
RUN mkdir -p ${APP_HOME}/data

# Copy backend application source and frontend static assets
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Set ownership to non-root user
RUN chown -R appuser:appgroup ${APP_HOME}

# Switch to non-root user
USER appuser

# Expose internal application port
EXPOSE 8000

# Healthcheck monitoring
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Launch application via Uvicorn
WORKDIR ${APP_HOME}/backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
