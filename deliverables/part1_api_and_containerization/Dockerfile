FROM python:3.10-slim

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry==1.8.3

# Copy dependency files
COPY pyproject.toml poetry.lock poetry.toml ./

# Install main dependencies only (skip dev group for production image)
RUN poetry install --only main --no-root --no-interaction

# Copy application source
COPY source/ ./source/
COPY deliverables/part1_api_and_containerization/app/ ./app/

# Make source package importable as `from source.application.graph import workflow`
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
