#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
PYTHON_BIN="${PYTHON_BIN:-${BACKEND_DIR}/.venv/bin/python}"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Backend virtual environment not found: ${PYTHON_BIN}" >&2
  echo "Create it and install backend/requirements-dev.txt first." >&2
  exit 1
fi

cd "${ROOT_DIR}"
docker compose up -d --wait mysql

if [[ ! -f "${BACKEND_DIR}/.env" ]]; then
  cp "${BACKEND_DIR}/.env.example" "${BACKEND_DIR}/.env"
  echo "Created backend/.env from backend/.env.example"
fi

cd "${BACKEND_DIR}"
"${PYTHON_BIN}" -m alembic upgrade head
"${PYTHON_BIN}" -m app.seed.seed_demo
"${PYTHON_BIN}" -m alembic check

echo "Database is ready: MySQL ai_moderation at 127.0.0.1:3306"
