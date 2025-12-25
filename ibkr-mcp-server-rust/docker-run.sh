#!/bin/bash
# Build and run Docker container

set -e

echo "Building Docker image..."
docker build -t ibkr-mcp-server-rust:latest .

echo ""
echo "Running container..."
docker run -d \
  --name ibkr-mcp-server \
  -p 8080:8080 \
  --env-file .env \
  ibkr-mcp-server-rust:latest

echo ""
echo "Container started successfully!"
echo "Health check: curl http://localhost:8080/health"
echo ""
echo "View logs: docker logs -f ibkr-mcp-server"
echo "Stop container: docker stop ibkr-mcp-server"
echo "Remove container: docker rm ibkr-mcp-server"
