#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
umask 077
command -v age >/dev/null
test -s secrets/backup_recipient
mkdir -p backups/encrypted runtime/metrics
exec 9>backups/.production.lock
flock -n 9 || exit 0
compose=(docker compose -f "${EDU_COMPOSE_FILE:-docker-compose.prod.yml}")
target="backups/encrypted/educapilote-$(date -u +%Y%m%dT%H%M%SZ)-$$.sql.gz.age"
partial="$target.partial"
trap 'rm -f -- "$partial"' EXIT
"${compose[@]}" exec -T postgres pg_dump -U postgres -d educapilote | gzip | age -R secrets/backup_recipient > "$partial"
test -s "$partial"
mv -- "$partial" "$target"
sha256sum "$target" > "$target.sha256"
printf 'edu_backup_last_success_timestamp_seconds %s\n' "$(date +%s)" > runtime/metrics/backup.prom.tmp
chmod 644 runtime/metrics/backup.prom.tmp
mv runtime/metrics/backup.prom.tmp runtime/metrics/backup.prom
# Only known encrypted artifacts in this fixed directory; never follow symlinks.
find backups/encrypted -maxdepth 1 -type f -name 'educapilote-*.sql.gz.age*' -mtime +14 -delete
printf '%s\n' "$target"
