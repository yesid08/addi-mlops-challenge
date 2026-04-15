# ── Stage 1: lint gate ──────────────────────────────────────────────────────
FROM python:3.10-slim AS lint

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry==1.8.3

# Copy dependency files
COPY pyproject.toml poetry.lock poetry.toml ./

# Install ALL deps (including dev group: ruff, mypy) for the lint check
RUN poetry install --no-root --no-interaction

# Copy application source and lint script
COPY source/ ./source/
COPY deliverables/part1_api_and_containerization/ ./deliverables/part1_api_and_containerization/
COPY scripts/lint.sh ./scripts/lint.sh

ENV PYTHONPATH=/app

# Fail the build if linting or type-checking does not pass
RUN bash scripts/lint.sh

# ── Stage 2: production image ─────────────────────────────────────────────────
FROM python:3.10-slim AS production

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry==1.8.3

# Copy dependency files
COPY pyproject.toml poetry.lock poetry.toml ./

# Install main dependencies only (linters are NOT shipped in production)
RUN poetry install --only main --no-root --no-interaction

# Copy application source
COPY source/ ./source/
COPY deliverables/part1_api_and_containerization/app/ ./app/

# Make source package importable as `from source.application.graph import workflow`
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
