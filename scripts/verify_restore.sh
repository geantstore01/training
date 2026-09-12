#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
compose=(docker compose -f docker-compose.dev.yml)
database="edu_restore_$(date -u +%Y%m%d%H%M%S)_$$"
[[ "$database" =~ ^edu_restore_[0-9]+_[0-9]+$ ]]
backup="$(bash scripts/backup.sh)"
"${compose[@]}" exec -T postgres createdb -U postgres "$database"
trap '"${compose[@]}" exec -T postgres dropdb -U postgres "$database"' EXIT
gzip -dc "$backup" | "${compose[@]}" exec -T postgres psql -q -U postgres -d "$database" -v ON_ERROR_STOP=1
"${compose[@]}" exec -T postgres psql -U postgres -d "$database" -v ON_ERROR_STOP=1 <<'SQL'
DO $$ BEGIN
  IF (SELECT count(*) FROM pg_tables WHERE schemaname='public' AND tableowner='edu_migrator') <> 54 THEN
    RAISE EXCEPTION 'Restored table/owner count mismatch';
  END IF;
  IF (SELECT count(*) FROM curriculum_levels) <> 2 THEN RAISE EXCEPTION 'Seed count mismatch'; END IF;
  IF (SELECT version_num FROM alembic_version) <> '0011_cm2_fhs_catalogue' THEN RAISE EXCEPTION 'Revision mismatch'; END IF;
END $$;
SQL
printf 'Sauvegarde et restauration validées : %s\n' "$backup"
