# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

# Runtime deps for docker SDK (no docker daemon needed; we talk to host socket)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
RUN uv pip install --system --no-cache fastapi uvicorn[standard] pydantic \
    pydantic-settings python-frontmatter PyYAML mcp docker jsonschema starlette

COPY app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
