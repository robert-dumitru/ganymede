# syntax=docker/dockerfile:1
FROM python:3.13-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

FROM python:3.13-bookworm

# Install system dependencies for LaTeX and Chromium
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    # LaTeX dependencies for PDFExporter
    texlive-xetex \
    texlive-fonts-recommended \
    texlive-plain-generic \
    pandoc \
    # Cleanup to reduce image size
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv

# Install Chromium with system dependencies (must run as root before USER ganymede)
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN /app/.venv/bin/playwright install --with-deps chromium

# Set up non-root user
RUN useradd -m -u 1000 ganymede && \
    mkdir -p /tmp/ganymede && \
    chown -R ganymede:ganymede /tmp/ganymede

WORKDIR /app
COPY . /app/api

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    WORKDIR=/tmp/ganymede

USER ganymede
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthcheck')"
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
