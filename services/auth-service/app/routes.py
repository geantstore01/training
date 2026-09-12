from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select, func

from shared.db.models import User
from shared.db.session import tenant_session
from shared.security.api import current_principal, enforce_rate, subject_state
from shared.security.passwords import hash_password, verify_password
from shared.security.policy import audit
from shared.security.sessions import unpack_refresh
from shared.security.tokens import Principal
from .schemas import LoginRequest, PasswordChange, PublicKeys, RefreshRequest, SessionIdentity, TokenPair

router = APIRouter(tags=["auth"])


def pair(request, principal, refresh):
    return TokenPair(access_token=request.app.state.tokens.issue(principal), refresh_token=refresh,
        expires_in=request.app.state.settings.access_token_seconds)


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, request: Request):
    enforce_rate(request, "login-account", f"{payload.school_id}:{payload.login}", 5)
    enforce_rate(request, "login-source", request.client.host if request.client else "unknown", 60)
    with tenant_session(request.app.state.engine, payload.school_id) as session:
        user = session.scalar(select(User).where(User.login == payload.login))
        valid = verify_password(user.password_hash if user else None, payload.password.get_secret_value())
        state = subject_state(session, user.id) if user else None
        if not valid or state is None or not state[1]:
            raise HTTPException(401, "Identifiants invalides.", headers={"WWW-Authenticate": "Bearer"})
        version, roles = state
        sid, refresh = request.app.state.sessions.create(user.id, payload.school_id, version,
            request.app.state.settings.refresh_token_seconds)
        principal = Principal(user_id=user.id, school_id=payload.school_id, roles=roles, session_id=sid, auth_version=version)
        user.last_login_at = func.now()
        audit(session, principal, "auth.login", "user", user.id)
    return pair(request, principal, refresh)


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, request: Request):
    denied = HTTPException(401, "Session invalide ou expirée.")
    token = payload.refresh_token.get_secret_value()
    try:
        sid = unpack_refresh(token)
    except (ValueError, TypeError):
        raise denied from None
    enforce_rate(request, "refresh", sid, 20)
    family = request.app.state.sessions.read(sid)
    if not family or family.get("revoked") != "0":
        raise denied
    school, user_id = UUID(family["school"]), UUID(family["user"])
    with tenant_session(request.app.state.engine, school) as session:
        state = subject_state(session, user_id)
        if state is None or state[0] != int(family["version"]) or not state[1]:
            request.app.state.sessions.revoke(sid)
            raise denied
        principal = Principal(user_id=user_id, school_id=school, roles=state[1], session_id=sid, auth_version=state[0])
        status, new_refresh = request.app.state.sessions.rotate(token)
        if status == "ok":
            audit(session, principal, "auth.refresh", "user", user_id)
        elif status == "reuse":
            audit(session, principal, "auth.refresh_reuse", "user", user_id)
    if status != "ok":
        # La révocation Redis et son audit sont conservés malgré la réponse 401.
        raise denied
    return pair(request, principal, new_refresh)


@router.post("/logout", status_code=204)
def logout(request: Request, principal: Principal = Depends(current_principal)):
    request.app.state.sessions.revoke(principal.session_id)
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        audit(session, principal, "auth.logout", "user", principal.user_id)
    return Response(status_code=204)


@router.post("/logout-all", status_code=204)
def logout_all(request: Request, principal: Principal = Depends(current_principal)):
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        user = session.scalar(select(User).where(User.id == principal.user_id).with_for_update())
        user.auth_version += 1
        audit(session, principal, "auth.logout_all", "user", principal.user_id)
    return Response(status_code=204)


@router.post("/password", status_code=204)
def change_password(payload: PasswordChange, request: Request, principal: Principal = Depends(current_principal)):
    enforce_rate(request, "password", principal.user_id, 5)
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        user = session.scalar(select(User).where(User.id == principal.user_id).with_for_update())
        if not verify_password(user.password_hash, payload.current_password.get_secret_value()):
            raise HTTPException(401, "Mot de passe actuel incorrect.")
        if payload.current_password.get_secret_value() == payload.new_password.get_secret_value():
            raise HTTPException(422, "Choisis un nouveau mot de passe.")
        user.password_hash = hash_password(payload.new_password.get_secret_value())
        user.auth_version += 1
        audit(session, principal, "auth.password_changed", "user", user.id)
    return Response(status_code=204)


@router.get("/me", response_model=SessionIdentity)
def me(principal: Principal = Depends(current_principal)):
    return SessionIdentity(user_id=principal.user_id, school_id=principal.school_id,
        roles=sorted(principal.roles), session_id=principal.session_id)


@router.get("/.well-known/jwks.json", response_model=PublicKeys)
def jwks(request: Request):
    return request.app.state.tokens.jwks()
