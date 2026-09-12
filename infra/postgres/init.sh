#!/bin/sh
set -eu
# Secrets générés en hexadécimal ; jamais interpolés sans contrôle.
for role in migrator auth user class curriculum content exercise assessment tutor retrieval speech notification analytics admin safety ai_router; do
  password="$(cat "/run/secrets/db_$role")"
  case "$password" in *[!a-zA-Z0-9]*|'') echo 'Invalid DB secret format' >&2; exit 1;; esac
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set=role="edu_$role" --set=password="$password" <<'SQL'
CREATE ROLE :"role" LOGIN PASSWORD :'password' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
SQL
done
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<'SQL'
CREATE EXTENSION IF NOT EXISTS vector;
CREATE ROLE edu_runtime NOLOGIN NOSUPERUSER NOBYPASSRLS;
REVOKE ALL ON DATABASE educapilote FROM PUBLIC;
GRANT CONNECT ON DATABASE educapilote TO edu_migrator, edu_runtime;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA public TO edu_migrator;
GRANT USAGE ON SCHEMA public TO edu_runtime;
GRANT edu_runtime TO edu_auth, edu_user, edu_class, edu_curriculum, edu_content,
 edu_exercise, edu_assessment, edu_tutor, edu_retrieval, edu_speech,
 edu_notification, edu_analytics, edu_admin, edu_safety, edu_ai_router;
ALTER ROLE edu_migrator SET lock_timeout = '10s';
ALTER ROLE edu_migrator SET statement_timeout = '120s';
ALTER ROLE edu_runtime SET idle_in_transaction_session_timeout = '15s';
SQL
