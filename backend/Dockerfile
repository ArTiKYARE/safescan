# ==========================================
# SafeScan Backend — Dockerfile
# ==========================================

FROM python:3.12-slim AS base

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-xlib-2.0-0 \
    shared-mime-info \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Configure pip with alternative mirrors
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set global.trusted-host mirrors.aliyun.com

# Install Python dependencies
COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
        --default-timeout=300 --retries 5 && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt \
        --default-timeout=300 --retries 5

# Copy application code
COPY . .

ENV PATH=/opt/venv/bin:$PATH
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--loop", "uvloop"]
