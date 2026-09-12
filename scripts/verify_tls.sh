#!/usr/bin/env bash
# Certificat de test local éphémère ; ne remplace aucun certificat de production.
set -euo pipefail
cd "$(dirname "$0")/.."
tls="$(mktemp -d /tmp/educapilote-tls.XXXXXX)"
container="educapilote-tls-check-$$"
cleanup() {
  docker rm -f "$container" >/dev/null 2>&1 || true
  case "$tls" in /tmp/educapilote-tls.*) rm -rf -- "$tls";; esac
}
trap cleanup EXIT
openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj /CN=localhost \
  -addext subjectAltName=DNS:localhost -keyout "$tls/privkey.pem" -out "$tls/fullchain.pem" 2>/dev/null
chmod 755 "$tls"
chmod 644 "$tls/fullchain.pem"
chown 101:101 "$tls/privkey.pem"
chmod 600 "$tls/privkey.pem"
export EDU_TLS_DIR="$tls"
compose=(docker compose -f docker-compose.dev.yml -f docker-compose.prod.yml)
"${compose[@]}" config --quiet
"${compose[@]}" run --rm --no-deps --entrypoint nginx proxy -t
"${compose[@]}" run -d --no-deps --name "$container" -p 127.0.0.1::8443 --entrypoint nginx proxy -g 'daemon off;'
port="$(docker port "$container" 8443/tcp | sed 's/.*://')"
curl --fail --silent --show-error --retry 5 --retry-connrefused --retry-delay 1 \
  --cacert "$tls/fullchain.pem" "https://localhost:$port/health/live"
printf '\nTLS validé sur un port local temporaire.\n'
