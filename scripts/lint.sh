#!/usr/bin/env bash
set -euo pipefail

echo "==> ruff: linting..."
poetry run ruff check .

echo "==> ruff: format check..."
poetry run ruff format --check .

echo "==> mypy: type-checking..."
poetry run mypy source/ deliverables/part1_api_and_containerization/app/ --ignore-missing-imports --exclude source/examples

echo "All checks passed."
