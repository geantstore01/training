#!/usr/bin/env bash
# Local TLS fixture only. This does NOT validate Let's Encrypt or public DNS.
set -euo pipefail
cd "$(dirname "$0")/.."
directory="$(mktemp -d "$PWD/runtime/tls-check.XXXXXX")"
container="educapilote-tls-check-$$"
trap 'docker rm -f "$container" >/dev/null 2>&1 || true; rm -rf -- "$directory"' EXIT
openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj /CN=educapilote.test \
  -addext subjectAltName=DNS:educapilote.test -keyout "$directory/key.pem" -out "$directory/cert.pem" >/dev/null 2>&1
python3 - "$directory" <<'PY'
from pathlib import Path
import sys
content = Path('infra/traefik/dynamic.yml').read_text()
content = content.replace('      tls:\n        certResolver: le','      tls: {}')
content = content.replace('\ntls:\n','\ntls:\n  certificates:\n    - certFile: /fixture/cert.pem\n      keyFile: /fixture/key.pem\n')
Path(sys.argv[1],'dynamic.yml').write_text(content)
PY
chmod 600 "$directory/key.pem"
chown -R 10001:10001 "$directory"
image="$(python3 -c 'import json; print("traefik:v3.7.13@"+json.load(open("infra/production-images.lock.json"))["traefik:v3.7.13"])')"
docker run --rm -d --name "$container" --network educapilote_backend \
  --user 10001:10001 --read-only --cap-drop ALL --security-opt no-new-privileges:true \
  -p 127.0.0.1:18443:8443 -e EDU_DOMAIN=educapilote.test -v "$directory:/fixture:ro" \
  "$image" --entrypoints.websecure.address=:8443 --providers.file.filename=/fixture/dynamic.yml \
  --log.level=WARN >/dev/null
docker network connect educapilote_edge "$container"
for attempt in $(seq 1 20); do
  if curl --noproxy '*' --silent --fail --cacert "$directory/cert.pem" \
    --resolve educapilote.test:18443:127.0.0.1 https://educapilote.test:18443/connexion -o "$directory/page.html"; then break; fi
  sleep 1
done
if [[ ! -s "$directory/page.html" ]]; then
  docker logs --tail 20 "$container" >&2
  echo 'Local TLS fixture failed; no public certificate was attempted.' >&2
  exit 1
fi
grep -q 'nonce=' "$directory/page.html"
status="$(curl --noproxy '*' --silent --cacert "$directory/cert.pem" --resolve educapilote.test:18443:127.0.0.1 \
  https://educapilote.test:18443/services/user-service/metrics -o /dev/null -w '%{http_code}')"
test "$status" = 404
printf 'PASS: real Traefik TLS handshake, Next.js routing, nonce CSP markup and no public service metrics. Certificate is a test fixture, not ACME.\n'
