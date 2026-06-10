FROM python:3.10-slim

WORKDIR /app

# Install git since the MCP server executes git CLI commands
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy the sub-package files to the container
COPY . /app

# Install the package in editable/runnable mode
RUN pip install --no-cache-dir .

# Expose port for optional SSE deployment mode
EXPOSE 8000

# Default entry point for standard I/O execution
ENTRYPOINT ["python3", "-m", "src.api.mcp.server"]
