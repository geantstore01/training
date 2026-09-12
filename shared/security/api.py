import hashlib
import hmac
from contextlib import contextmanager

import jwt
from cryptography.exceptions import InvalidTag
from fastapi import Depends, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.exceptions import RedisError
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from shared.db.models import School, Tenant, User, UserRole
from shared.db.session import tenant_session
from shared.security.sessions import SessionStore
from shared.security.tokens import Principal, TokenCodec

bearer = HTTPBearer(auto_error=False)


class ValidationIssue(BaseModel):
    loc: list[str | int]
    type: str


class ErrorResponse(BaseModel):
    detail: str
    errors: list[ValidationIssue] | None = None


ERROR_RESPONSES = {code: {"model": ErrorResponse, "description": description} for code, description in {
    401: "Session invalide", 403: "Accès interdit", 404: "Ressource introuvable", 409: "Conflit",
    413: "Requête trop volumineuse", 422: "Validation refusée", 429: "Limite atteinte", 503: "Dépendance indisponible"}.items()}

LIMIT = """
local count=redis.call('INCR',KEYS[1])
if count==1 then redis.call('EXPIRE',KEYS[1],ARGV[1]) end
return count
"""


def initialize_access(app, *, signing=False):
    app.state.tokens = TokenCodec(app.state.settings, signing=signing)
    app.state.sessions = SessionStore(app.state.cache)
    app.state.rate_key = app.state.settings.rate_key_file.read_bytes()


def enforce_rate(request, category, identity, limit, seconds=60):
    name = request.app.state.settings.service_name.removesuffix("-service")
    hashed = hmac.new(request.app.state.rate_key, str(identity).encode(), hashlib.sha256).hexdigest()
    count = request.app.state.cache.eval(LIMIT, 1, f"edu:rate:{name}:{category}:{hashed}", seconds)
    if count > limit:
        raise HTTPException(429, "Trop de tentatives. Réessaie plus tard.", headers={"Retry-After": str(seconds)})


def subject_state(session, user_id):
    row = session.execute(select(User.id, User.status, User.auth_version, User.deleted_at)
        .join(School, School.id == User.tenant_id).join(Tenant, Tenant.id == School.tenant_id)
        .where(User.id == user_id, Tenant.status == "active")).one_or_none()
    if row is None or row.status != "active" or row.deleted_at is not None:
        return None
    roles = frozenset(session.scalars(select(UserRole.role).where(UserRole.user_id == user_id)))
    return row.auth_version, roles


def current_principal(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> Principal:
    denied = HTTPException(401, "Session invalide ou expirée.", headers={"WWW-Authenticate": "Bearer"})
    if credentials is None or len(credentials.credentials) > 8192:
        raise denied
    try:
        principal = request.app.state.tokens.verify(credentials.credentials)
    except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
        raise denied from None
    family = request.app.state.sessions.read(principal.session_id)
    if not family or family.get("revoked") != "0" or family.get("user") != str(principal.user_id) or family.get("school") != str(principal.school_id) or family.get("version") != str(principal.auth_version):
        raise denied
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        state = subject_state(session, principal.user_id)
    if state is None or state != (principal.auth_version, principal.roles):
        raise denied
    return principal


def require_roles(*roles):
    def dependency(principal: Principal = Depends(current_principal)):
        if not principal.roles.intersection(roles):
            raise HTTPException(403, "Action non autorisée.")
        return principal
    return dependency


class BodyLimitMiddleware:
    def __init__(self, app, limit=32768):
        self.app, self.limit = app, limit

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > self.limit:
                return await JSONResponse({"detail": "Requête trop volumineuse."}, status_code=413)(scope, receive, send)
            if not message.get("more_body", False):
                break
        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        async def private_send(message):
            if message["type"] == "http.response.start":
                message["headers"] = [*message.get("headers", []), (b"cache-control", b"no-store")]
            await send(message)
        await self.app(scope, replay, private_send)


def harden_app(app):
    app.add_middleware(BodyLimitMiddleware)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, exc):
        # FastAPI inclut normalement l'entrée rejetée : jamais pour des identités/mots de passe.
        return JSONResponse(status_code=422, content={"detail": "Données invalides.",
            "errors": [{"loc": list(item["loc"]), "type": item["type"]} for item in exc.errors()]})

    async def unavailable(request, exc):
        return JSONResponse(status_code=503, content={"detail": "Service temporairement indisponible."})

    app.add_exception_handler(RedisError, unavailable)
    app.add_exception_handler(SQLAlchemyError, unavailable)
    app.add_exception_handler(InvalidTag, unavailable)

    @app.exception_handler(IntegrityError)
    async def conflict(request, exc):
        return JSONResponse(status_code=409, content={"detail": "Conflit ou contrainte de données."})
