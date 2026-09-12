#!/usr/bin/env bash
# Vérification dans une base neuve, créée et supprimée par ce script uniquement.
set -euo pipefail
cd "$(dirname "$0")/.."
compose=(docker compose -f docker-compose.dev.yml)
database="edu_verify_$(date -u +%Y%m%d%H%M%S)_$$"
[[ "$database" =~ ^edu_verify_[0-9]+_[0-9]+$ ]]
"${compose[@]}" exec -T postgres createdb -U postgres -O edu_migrator "$database"
trap '"${compose[@]}" exec -T postgres dropdb -U postgres "$database"' EXIT
"${compose[@]}" exec -T postgres psql -U postgres -d "$database" -v ON_ERROR_STOP=1 <<'SQL'
CREATE EXTENSION vector;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO edu_runtime;
SQL
for action in 'upgrade head' 'check' 'downgrade base' 'upgrade head' 'check'; do
  read -r -a arguments <<< "$action"
  "${compose[@]}" run --rm --no-deps -e "EDU_DB_NAME=$database" migrate alembic "${arguments[@]}"
done
"${compose[@]}" exec -T postgres psql -U postgres -d "$database" -v ON_ERROR_STOP=1 <<'SQL'
DO $$ BEGIN
  IF (SELECT count(*) FROM curriculum_levels) <> 2 THEN RAISE EXCEPTION 'Seed count mismatch'; END IF;
  IF (SELECT version_num FROM alembic_version) <> '0011_cm2_fhs_catalogue' THEN RAISE EXCEPTION 'Revision mismatch'; END IF;
END $$;
SQL
printf 'Migration, downgrade et réapplication validés dans une base isolée.\n'
