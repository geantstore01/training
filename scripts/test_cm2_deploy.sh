#!/usr/bin/env bash
# Tous les tests métier utilisent une base éphémère ; aucune fixture dans la base active.
set -euo pipefail
cd "$(dirname "$0")/.."
compose=(docker compose -f docker-compose.dev.yml)
database="edu_module56_test_$(date -u +%Y%m%d%H%M%S)_$$"
[[ "$database" =~ ^edu_module56_test_[0-9]+_[0-9]+$ ]]

"${compose[@]}" build migrate test
"${compose[@]}" exec -T postgres createdb -U postgres -O edu_migrator "$database"
trap '"${compose[@]}" exec -T postgres dropdb -U postgres "$database"' EXIT
"${compose[@]}" exec -T postgres psql -U postgres -d "$database" -v ON_ERROR_STOP=1 <<'SQL'
CREATE EXTENSION vector;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO edu_runtime;
SQL
"${compose[@]}" run --rm --no-deps -e "EDU_DB_NAME=$database" migrate alembic upgrade head
"${compose[@]}" run --rm --no-deps -e "EDU_DB_NAME=$database" migrate alembic check
"${compose[@]}" --profile test run --rm --no-deps -e "EDU_TEST_DB_NAME=$database" test python -m pytest -q -p no:cacheprovider "$@"
