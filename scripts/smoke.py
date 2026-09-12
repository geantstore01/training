"""Vérifie les 15 services via le vrai proxy, sans données personnelles."""
import argparse
import json
from pathlib import Path
from urllib.request import urlopen

parser = argparse.ArgumentParser()
parser.add_argument("--base-url", default="http://127.0.0.1:18088")
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
services = sorted((root / "services").iterdir())
results = []
for service in services:
    if not service.is_dir():
        continue
    prefix = f"{args.base_url.rstrip('/')}/services/{service.name}"
    with urlopen(prefix + "/health/ready", timeout=10) as response:
        health = json.load(response)
    assert health == {"status": "ok", "service": service.name, "module": "infrastructure", "postgres": True, "redis": True}, service.name
    with urlopen(prefix + "/openapi.json", timeout=10) as response:
        actual = json.load(response)
    expected = json.loads((service / "openapi.json").read_text(encoding="utf-8"))
    assert actual == expected, f"Contrat divergent : {service.name}"
    results.append({"service": service.name, "ready": True, "openapi_matches": True})
assert len(results) == 15
print(json.dumps(results, ensure_ascii=False, indent=2))
