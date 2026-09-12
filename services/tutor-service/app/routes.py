from shared.ai.history_teacher_prompt import INSUFFICIENT_HISTORY_CONTEXT
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError
from sqlalchemy import delete, select, text, func
from shared.ai.context import attempt_context, passages
from shared.ai.contracts import Plan, SearchResponse, TutorRequest, TutorResponse
from shared.ai.pedagogy import ALLOWED, bypass, render
from shared.ai.french_policy import INSUFFICIENT_FRENCH_CONTEXT
from shared.ai.science_policy import INSUFFICIENT_SCIENCE_CONTEXT
from shared.ai.transport import DependencyFailure, headers, post, safety
from shared.db.models import TutorTurn, Hint
from shared.school import tutor_limit
from shared.db.session import tenant_session
from shared.security.api import current_principal, enforce_rate

router = APIRouter()

def previous(session, attempt_id):
    return session.scalar(select(TutorTurn).where(TutorTurn.attempt_id == attempt_id)
        .order_by(TutorTurn.created_at.desc(), TutorTurn.id.desc()).limit(1))

def replay(session, body, digest):
    row = session.scalar(select(TutorTurn).where(TutorTurn.attempt_id == body.attempt_id, TutorTurn.request_id == body.request_id))
    if row:
        if not hmac.compare_digest(row.request_digest, digest):
            raise HTTPException(409, "Identifiant de requête déjà utilisé.")
        return TutorResponse.model_validate(row.response)

@router.post("/turns", response_model=TutorResponse)
def turn(body: TutorRequest, request: Request, principal=Depends(current_principal)):
    enforce_rate(request, "turn", principal.user_id, 20)
    settings = request.app.state.settings
    message = body.message.get_secret_value()
    digest = hmac.new(request.app.state.rate_key, json.dumps([str(body.attempt_id), message, body.plus_aide], ensure_ascii=False).encode(), hashlib.sha256).hexdigest()
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        # Après la correction, l'élève peut demander une explication. Cette aide
        # est consultative : elle ne modifie ni réponse ni score.
        attempt, level, subject, query = attempt_context(session, principal, body.attempt_id, include_submitted=True)
        session.execute(delete(TutorTurn).where(TutorTurn.expires_at < datetime.now(timezone.utc)))
        cached = replay(session, body, digest)
        if cached:
            return cached if cached.niveau_aide <= tutor_limit(session, attempt.student_id) else render(tutor_limit(session, attempt.student_id))
        old = previous(session, body.attempt_id)
        old_id, old_level = (old.id, old.level) if old else (None, 0)
        target_level = min(old_level + int(body.plus_aide and old is not None and old.response["safety_status"] == "safe"), tutor_limit(session, attempt.student_id))
        if attempt.submitted_at and tutor_limit(session,attempt.student_id)>0:
            target_level=max(1,target_level)
        authored_max=session.scalar(select(func.max(Hint.level)).where(Hint.exercise_version_id==attempt.exercise_version_id)) or 0
        help_ceiling=min(tutor_limit(session,attempt.student_id),authored_max if authored_max>=2 else 6)
        target_level=min(target_level,help_ceiling)
        old_level = min(old_level, tutor_limit(session, attempt.student_id))
        student_id = attempt.student_id
        authored_hint = session.scalar(select(Hint).where(Hint.exercise_version_id==attempt.exercise_version_id,
            Hint.level==target_level).limit(1)) if target_level else None
        hint_text = authored_hint.body["text"] if authored_hint else None
    ids = []
    try:
        clean = safety(request, message, student_id, "local")
        if bypass(message):
            result = render(old_level, refusal=True)
            if subject in {"francais","sciences","histoire"}:
                result.message_pedagogique="Tu peux réfléchir avec les indices ou utiliser le bouton Demander la correction pour consulter un exemple expliqué."
                result.question_suivante=None
        elif hint_text:
            result = render(target_level)
            result.message_pedagogique = hint_text
            result.question_suivante = "Quelle étape peux-tu essayer avec cet indice ?"
        else:
            scope={}
            if subject=="histoire" and level=="CM2":
                from shared.history.catalogue import COURSES
                chapter=next((e["chapter"] for e in COURSES if e["title"]==query),None)
                if not chapter:raise DependencyFailure("unknown_history_chapter")
                scope["history_chapter"]=chapter
            query = safety(request, query, student_id, "local")
            # La requête porte sur les compétences de l'exercice, jamais sur un corrigé privé.
            found = SearchResponse.model_validate(post(settings.retrieval_url + "/search", {"query": query, "level": level, "subject": subject, "limit": 3, **scope}, headers(request, private=True)))
            ids = [item.id for item in found.passages]
            if not ids:
                raise DependencyFailure("no_validated_source")
            plan = Plan.model_validate(post(settings.router_url + "/plan", {"attempt_id": str(body.attempt_id), "message": clean,
                "niveau": target_level, "passage_ids": [str(id) for id in ids]}, headers(request, private=True), timeout=45))
            if plan.source_id not in ids or plan.action not in ALLOWED[target_level]:
                raise DependencyFailure("invalid_plan")
            ids = [plan.source_id]
            result = render(target_level, plan.action, plan.erreur)
    except HTTPException as exc:
        if exc.status_code != 403:
            raise
        ids, result = [], render(old_level, protection=True)
        if "consentement" in str(exc.detail):
            # Refus lié aux accords parent/élève : dire précisément ce qu'il faut activer
            # plutôt qu'un message de protection générique qui inquiète sans expliquer.
            result.message_pedagogique = ("Pour que je puisse te répondre, l’aide « Aide IA locale » doit être "
                "autorisée par ton représentant puis activée dans « Mes choix de confidentialité ».")
        elif "suspendu par l'enseignant" in str(exc.detail):
            result.message_pedagogique = "Ton enseignant a mis l’aide IA en pause pour le moment. Continue avec les indices du parcours."
    except DependencyFailure as exc:
        ids, result = [], render(old_level, protection=exc.status == 403, unavailable=exc.status != 403)
    except ValidationError:
        ids, result = [], render(old_level, unavailable=True)
    result.aide_max=help_ceiling
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        # Même verrou que la correction, afin de sérialiser les aides d'une tentative.
        session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key,0))"), {"key": f"assessment:{principal.school_id}:{principal.user_id}"})
        attempt, level, subject, _ = attempt_context(session, principal, body.attempt_id, include_submitted=True)
        cached = replay(session, body, digest)
        if cached:
            return cached if cached.niveau_aide <= tutor_limit(session, attempt.student_id) else render(tutor_limit(session, attempt.student_id))
        latest = previous(session, body.attempt_id)
        if (latest.id if latest else None) != old_id:
            raise HTTPException(409, "Une autre aide a été enregistrée. Réessaie.")
        if ids and len(passages(session, ids, level, subject, settings.embedding_model)) != len(ids):
            ids, result = [], render(old_level, unavailable=True)
        limit = tutor_limit(session, attempt.student_id)
        if result.niveau_aide > limit: result = render(limit)
        if subject in {"francais","sciences","histoire"} and result.type=="indisponible":
            result.message_pedagogique=INSUFFICIENT_HISTORY_CONTEXT if subject=="histoire" else INSUFFICIENT_SCIENCE_CONTEXT if subject=="sciences" else INSUFFICIENT_FRENCH_CONTEXT
            result.question_suivante=None
        if not attempt.submitted_at:
            attempt.max_hint_level = max(attempt.max_hint_level, result.niveau_aide)
        session.add(TutorTurn(tenant_id=principal.school_id, attempt_id=body.attempt_id, request_id=body.request_id,
            request_digest=digest, level=result.niveau_aide, response=result.model_dump(), passage_ids=[str(id) for id in ids],
            expires_at=datetime.now(timezone.utc)+timedelta(days=7)))
        session.execute(delete(TutorTurn).where(TutorTurn.expires_at < datetime.now(timezone.utc)))
        return result

@router.get("/attempts/{attempt_id}/history", response_model=list[TutorResponse])
def history(attempt_id: UUID, request: Request, principal=Depends(current_principal)):
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        attempt, _, _, _ = attempt_context(session, principal, attempt_id, include_submitted=True)
        limit = tutor_limit(session, attempt.student_id)
        rows = session.scalars(select(TutorTurn.response).where(TutorTurn.attempt_id == attempt_id, TutorTurn.level <= limit, TutorTurn.expires_at > datetime.now(timezone.utc))
            .order_by(TutorTurn.created_at.desc()).limit(50))
        return [TutorResponse.model_validate(row) for row in rows]
