"""Lie le daemon de l'hôte à la passerelle du backend interne, sans ouvrir le réseau."""
import ipaddress
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
result = subprocess.run(["docker", "network", "inspect", "educapilote_backend"], capture_output=True, text=True, check=True)
gateway = json.loads(result.stdout)[0]["IPAM"]["Config"][0]["Gateway"]
address = ipaddress.ip_address(gateway)
if not address.is_private or address.version != 4:
    raise ValueError("Passerelle IPv4 privée requise")
path = root / ".env"
lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
lines = [line for line in lines if not line.startswith("EDU_OLLAMA_HOST_IP=")]
path.write_bytes(("\n".join([*lines, "EDU_OLLAMA_HOST_IP="+gateway])+"\n").encode())
print("Adresse de liaison Ollama configurée : " + gateway)
