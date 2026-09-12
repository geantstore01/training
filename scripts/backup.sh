#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
umask 077
mkdir -p backups
target="backups/educapilote-$(date -u +%Y%m%dT%H%M%SZ)-$$.sql.gz"
partial="${target}.partial"
trap 'rm -f -- "$partial"' EXIT
docker compose -f docker-compose.dev.yml exec -T postgres pg_dump \
  --username=postgres --dbname=educapilote | gzip > "$partial"
gzip -t "$partial"
mv -- "$partial" "$target"
printf '%s\n' "$target"
