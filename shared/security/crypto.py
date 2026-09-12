import base64
import json
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class IdentityCipher:
    """Enveloppe AES-256-GCM versionnée et liée au propriétaire via AAD."""

    def __init__(self, path):
        payload = json.loads(path.read_text())
        self.active = payload["active"]
        decoded = {kid: base64.b64decode(key, validate=True) for kid, key in payload["keys"].items()}
        if any(len(key) != 32 for key in decoded.values()):
            raise ValueError("AES-256 keys required")
        self.keys = {kid: AESGCM(key) for kid, key in decoded.items()}
        if self.active not in self.keys:
            raise ValueError("Unknown active encryption key")

    def encrypt(self, data: dict, *, school_id, owner_id, purpose: str) -> bytes:
        nonce = secrets.token_bytes(12)
        aad = f"{school_id}:{owner_id}:{purpose}".encode()
        body = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode()
        ciphertext = self.keys[self.active].encrypt(nonce, body, aad)
        return json.dumps({"v": 1, "kid": self.active, "nonce": base64.b64encode(nonce).decode(),
            "ciphertext": base64.b64encode(ciphertext).decode()}, separators=(",", ":")).encode()

    def decrypt(self, envelope: bytes, *, school_id, owner_id, purpose: str) -> dict:
        payload = json.loads(envelope)
        if payload["v"] != 1:
            raise ValueError("Unsupported envelope")
        aad = f"{school_id}:{owner_id}:{purpose}".encode()
        plaintext = self.keys[payload["kid"]].decrypt(base64.b64decode(payload["nonce"], validate=True),
            base64.b64decode(payload["ciphertext"], validate=True), aad)
        return json.loads(plaintext)
