"""Clés aléatoires et mots de passe Redis du module 2. Aucune valeur affichée."""
import base64
import json
import os
from pathlib import Path
import secrets

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

root = Path(__file__).resolve().parents[1] / "secrets"
root.mkdir(mode=0o700, exist_ok=True)


def write_once(name, data):
    path = root / name
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return
    with os.fdopen(fd, "wb") as output:
        output.write(data)
    os.chmod(path, 0o444)


private_path = root / "jwt_private_key"
if private_path.exists():
    private = serialization.load_pem_private_key(private_path.read_bytes(), password=None)
else:
    private = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    write_once("jwt_private_key", private.private_bytes(serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
public = private.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
write_once("jwt_public_keys", json.dumps({"edu-key-1": public}).encode())
write_once("pii_keys", json.dumps({"active": "pii-key-1", "keys": {"pii-key-1": base64.b64encode(secrets.token_bytes(32)).decode()}}).encode())
write_once("rate_key", secrets.token_bytes(32))
for role in ["auth", "user", "safety", "curriculum", "content", "exercise", "assessment", "tutor", "retrieval", "ai-router", "class", "analytics", "admin", "speech", "notification", "web"]:
    write_once(f"redis_{role}", (secrets.token_hex(32) + "\n").encode())
print("Secrets du module 2 initialisés sans écrasement.")

write_once("ai_internal_key", (secrets.token_hex(32) + "\n").encode())

write_once("automation_keys", b"[]\n")
