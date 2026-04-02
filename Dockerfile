# Legal Anonymizer - Production Docker Image

FROM python:3.11-slim as builder

WORKDIR /build

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY engine/python/pyproject.toml engine/python/
RUN pip install --user -e engine/python[all]

# Download spaCy models
RUN python -m spacy download en_core_web_sm && \
    python -m spacy download nl_core_news_sm && \
    python -m spacy download de_core_news_sm

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy application code
COPY engine/python/ /app/engine/python/
COPY scripts/ /app/scripts/

# Set environment variables
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from anonymizer_engine import __version__; print(__version__)" || exit 1

# Run as non-root user
RUN useradd -m -u 1000 anonymizer && \
    chown -R anonymizer:anonymizer /app
USER anonymizer

# Default command
ENTRYPOINT ["python", "/app/scripts/sidecar_entrypoint.py"]
CMD ["--help"]
