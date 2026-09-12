#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
compose=(docker compose -f docker-compose.prod.yml)
"${compose[@]}" config --format json | python3 scripts/check_production.py
python3 scripts/init_production.py
"${compose[@]}" build
# Backup uses the running project before migration or application replacement.
EDU_COMPOSE_FILE=docker-compose.prod.yml bash scripts/backup_production.sh
"${compose[@]}" run --rm migrate
"${compose[@]}" up -d --wait --wait-timeout 240
echo 'Services started. Validate the publicly trusted certificate and E2E checklist before opening pupil access.'
