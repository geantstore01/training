import json
import time
from uuid import UUID, uuid4

import jwt
from cryptography.hazmat.primitives import serialization
from pydantic import BaseModel, ConfigDict

ROLES = frozenset({"student", "parent", "teacher", "school_admin", "content_creator", "sys_admin"})


class Principal(BaseModel):
    model_config = ConfigDict(frozen=True)
    user_id: UUID
    school_id: UUID
    roles: frozenset[str]
    session_id: UUID
    auth_version: int


class TokenCodec:
    def __init__(self, settings, *, signing=False):
        self.config = settings
        entries = json.loads(settings.jwt_public_keys_file.read_text())
        self.keys = {kid: serialization.load_pem_public_key(pem.encode()) for kid, pem in entries.items()}
        self.private = serialization.load_pem_private_key(settings.jwt_private_key_file.read_bytes(), password=None) if signing else None
        if signing and (settings.jwt_active_kid not in self.keys or
            self.private.public_key().public_numbers() != self.keys[settings.jwt_active_kid].public_numbers()):
            raise ValueError("Signing key does not match active public key")

    def issue(self, principal: Principal) -> str:
        now = int(time.time())
        return jwt.encode({"iss": self.config.jwt_issuer, "aud": self.config.jwt_audience,
            "sub": str(principal.user_id), "school_id": str(principal.school_id),
            "roles": sorted(principal.roles), "sid": str(principal.session_id),
            "ver": principal.auth_version, "iat": now, "nbf": now,
            "exp": now + self.config.access_token_seconds, "jti": str(uuid4()), "token_type": "access"},
            self.private, algorithm="RS256", headers={"kid": self.config.jwt_active_kid, "typ": "JWT"})

    def verify(self, token: str) -> Principal:
        header = jwt.get_unverified_header(token)
        if header.get("alg") != "RS256" or header.get("typ") != "JWT" or header.get("kid") not in self.keys:
            raise jwt.InvalidTokenError("Invalid token header")
        claims = jwt.decode(token, self.keys[header["kid"]], algorithms=["RS256"],
            issuer=self.config.jwt_issuer, audience=self.config.jwt_audience, leeway=5,
            options={"require": ["iss", "aud", "sub", "school_id", "roles", "sid", "ver", "iat", "nbf", "exp", "jti", "token_type"]})
        roles = claims["roles"]
        if claims["token_type"] != "access" or not isinstance(roles, list) or not roles or not set(roles) <= ROLES:
            raise jwt.InvalidTokenError("Invalid claims")
        if type(claims["ver"]) is not int or claims["ver"] < 1:
            raise jwt.InvalidTokenError("Invalid token version")
        UUID(claims["jti"])
        return Principal(user_id=claims["sub"], school_id=claims["school_id"], roles=frozenset(roles),
            session_id=claims["sid"], auth_version=claims["ver"])

    def jwks(self):
        return {"keys": [dict(json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(key)), kid=kid, use="sig", alg="RS256")
            for kid, key in self.keys.items()]}
