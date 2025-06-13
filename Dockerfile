FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY pyproject.toml ./
RUN pip install --no-cache-dir hatchling

# Install dependencies
RUN pip install --no-cache-dir .

# Copy source code
COPY src/ ./src/
COPY examples/ ./examples/
COPY README.md ./

# Install the package
RUN pip install --no-cache-dir -e .

# Create non-root user
RUN useradd --create-home --shell /bin/bash ibkr
USER ibkr

# Create logs directory
RUN mkdir -p /home/ibkr/logs

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the server
CMD ["ibkr-mcp-server", "serve"] 