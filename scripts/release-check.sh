#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR/apps/api"
python -m ruff check .
python -m pytest -q
python -m pip_audit -r requirements.txt

cd "$ROOT_DIR/apps/web"
npm run lint
npm run typecheck
rm -rf .next
npm run build
npm audit --audit-level=high
if grep -R "http://localhost:8000" .next/static .next/server >/dev/null 2>&1; then
  echo "Unsafe localhost API fallback found in Next production output."
  exit 1
fi

cd "$ROOT_DIR"
export SECRET_KEY="${SECRET_KEY:-release-check-secret-key-that-is-long-enough}"
export ENCRYPTION_KEY="${ENCRYPTION_KEY:-0J4FyJwHnYmeFz7r5Zk8F0KJxl-2mFY9hqqIetQxZj0=}"
export ADMIN_PASSWORD="${ADMIN_PASSWORD:-release-check-admin-password}"
docker compose -f docker-compose.yml config

if [[ "${RUN_DOCKER_BUILD:-0}" == "1" ]]; then
  docker compose -f docker-compose.yml build api worker web
fi
