FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml ./
COPY server.py ./
COPY run_server.py ./
COPY tools/ ./tools/
COPY utils/ ./utils/
COPY slide_layout_templates.json ./
COPY openapi.json ./
COPY openapi_optimized.json ./

# Install dependencies using uv
RUN uv pip install --system --no-cache chuk-mcp-server>=0.4.4 python-pptx>=0.6.21 Pillow>=8.0.0 fonttools>=4.0.0 'mcp>=1.3.0,<2.0.0' fastapi uvicorn

# Expose HTTP port
EXPOSE 8000

# Run server - HTTP wrapper for Fly.io compatibility
CMD ["python", "run_server.py"]
