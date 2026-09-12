#!/usr/bin/env bash
# Always restore into a NEW isolated database, never overwrite educapilote.
set -euo pipefail
cd "$(dirname "$0")/.."
[[ $# == 2 ]] || { echo 'Usage: restore_postgres.sh backup.sql.gz.age identity-file' >&2; exit 2; }
backup="$(realpath -- "$1")"
identity="$(realpath -- "$2")"
test -f "$backup" && test -f "$identity"
[[ "$backup" == *.sql.gz.age ]] || exit 2
compose=(docker compose -f "${EDU_COMPOSE_FILE:-docker-compose.prod.yml}")
database="edu_restore_$(date -u +%Y%m%d%H%M%S)_$$"
"${compose[@]}" exec -T postgres createdb -U postgres "$database"
complete=false
trap 'if [[ "$complete" != true ]]; then "${compose[@]}" exec -T postgres dropdb -U postgres "$database"; fi' EXIT
age -d -i "$identity" "$backup" | gzip -dc | "${compose[@]}" exec -T postgres psql -q -U postgres -d "$database" -v ON_ERROR_STOP=1 >/dev/null
"${compose[@]}" exec -T postgres psql -U postgres -d "$database" -v ON_ERROR_STOP=1 <<'SQL'
DO $$ BEGIN
  IF (SELECT version_num FROM alembic_version) <> '0011_cm2_fhs_catalogue' THEN RAISE EXCEPTION 'Revision mismatch'; END IF;
  IF (SELECT count(*) FROM pg_tables WHERE schemaname='public' AND tableowner='edu_migrator') <> 54 THEN RAISE EXCEPTION 'Table count mismatch'; END IF;
END $$;
SQL
complete=true
printf 'Restored database (kept for inspection): %s\n' "$database"
