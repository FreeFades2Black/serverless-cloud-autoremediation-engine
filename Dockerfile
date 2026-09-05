# Dockerfile for Serverless Cloud Auto-Remediation Engine
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt pytest boto3 moto

# Copy source code and tests
COPY src/ ./src/
COPY tests/ ./tests/

# Non-root user
RUN addgroup --gid 10005 remediation && \
    adduser --uid 10005 --gid 10005 --disabled-password --gecos "" remediation && \
    chown -R remediation:remediation /app

USER 10005:10005

# Run test suite by default
CMD ["python", "-m", "pytest", "tests/", "-v"]
