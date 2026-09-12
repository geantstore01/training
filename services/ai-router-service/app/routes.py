from shared.ai.history_teacher_prompt import HISTORY_TEACHER_PROMPT
from datetime import datetime, timedelta, timezone
import json
import time
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError
from sqlalchemy import null
from shared.ai.context import attempt_context, passages
from shared.ai.contracts import Plan, PlanRequest
from shared.ai.pedagogy import ALLOWED, PROMPT_VERSION, SYSTEM_PROMPT
from shared.ai.cm2_policy import CM2_TEACHER_PROMPT
from shared.ai.french_policy import FRENCH_TEACHER_PROMPT
from shared.ai.science_policy import SCIENCE_TEACHER_PROMPT
from shared.ai.transport import DependencyFailure, internal, post, safety
from shared.db.models import AIInteraction
from shared.db.session import tenant_session
from shared.security.api import current_principal, enforce_rate

router = APIRouter()

def validate_plan(content, level, source_ids):
    try:
        result = Plan.model_validate_json(content)
        if result.action not in ALLOWED[level] or result.source_id not in source_ids:
            raise ValueError("plan")
        return result
    except (ValidationError, ValueError, TypeError):
        raise DependencyFailure("provider_invalid_plan") from None

@router.post("/plan", response_model=Plan, dependencies=[Depends(internal)])
def plan(body: PlanRequest, request: Request, principal=Depends(current_principal)):
    settings = request.app.state.settings
    enforce_rate(request, "plan", principal.user_id, 12)
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        attempt, level, subject, _ = attempt_context(session, principal, body.attempt_id, include_submitted=True)
        from shared.school import tutor_limit
        if body.niveau > tutor_limit(session, attempt.student_id): raise HTTPException(403,"Niveau d’aide limité par l’enseignant.")
        student_id, session_id = attempt.student_id, attempt.session_id
        rows = passages(session, body.passage_ids, level, subject, settings.embedding_model)
    if len(rows) != len(set(body.passage_ids)):
        raise HTTPException(409, "Sources validées requises.")
    clean = safety(request, body.message.get_secret_value(), student_id, "cloud")
    sources = [{"id": str(row.id), "extrait": safety(request, row.body[:1000], student_id, "cloud")} for row in rows]
    # Quota prélevé AVANT chaque appel, y compris en cas d'échec, partagé entre workers.
    day = datetime.now(timezone.utc).date().isoformat()
    enforce_rate(request, "cloud_daily", f"{principal.school_id}:{day}", settings.ai_daily_calls, 172800)
    circuit = request.app.state.circuit
    circuit.check()
    started, outcome, input_tokens, output_tokens = time.monotonic(), "failed", 0, 0
    try:
        data = post(settings.ollama_url + "/api/chat", {"model": settings.cloud_model, "stream": False, "think": "low",
            "messages": [{"role": "system", "content": ((HISTORY_TEACHER_PROMPT if subject=="histoire" else SCIENCE_TEACHER_PROMPT if subject=="sciences" else FRENCH_TEACHER_PROMPT if subject=="francais" else CM2_TEACHER_PROMPT) + "\nPour cet appel de planification, ne produis pas une leçon : le serveur affiche les contenus validés.\n" if level == "CM2" and subject in {"mathematiques","francais","sciences","histoire"} else "") + SYSTEM_PROMPT}, {"role": "user", "content": json.dumps({
                "niveau": body.niveau, "actions_autorisees": sorted(ALLOWED[body.niveau]), "message": clean, "sources": sources}, ensure_ascii=False)}],
            "options": {"temperature": 0, "num_predict": 384}}, timeout=25, max_bytes=32768)
        if not isinstance(data, dict) or not isinstance(data.get("message"), dict):
            raise DependencyFailure("provider_invalid_plan")
        result = validate_plan(data["message"].get("content"), body.niveau, {row.id for row in rows})
        usage = [data.get("prompt_eval_count", 0), data.get("eval_count", 0)]
        if any(not isinstance(x, int) or isinstance(x, bool) or not 0 <= x <= 100000 for x in usage):
            raise DependencyFailure("provider_invalid_usage")
        input_tokens, output_tokens = usage
        outcome = "completed"
        return result
    finally:
        request.app.state.telemetry.ai_result(outcome, time.monotonic()-started, input_tokens, output_tokens)
        circuit.result(outcome == "completed")
        with tenant_session(request.app.state.engine, principal.school_id) as session:
            session.add(AIInteraction(tenant_id=principal.school_id, student_id=student_id, session_id=session_id,
                request_id=uuid4(), provider="cloud", model=settings.cloud_model, prompt_template_version=PROMPT_VERSION,
                hint_level=body.niveau, input_tokens=input_tokens if isinstance(input_tokens, int) else 0,
                output_tokens=output_tokens if isinstance(output_tokens, int) else 0, latency_ms=int((time.monotonic()-started)*1000),
                outcome=outcome, cost_eur=null(), expires_at=datetime.now(timezone.utc)+timedelta(days=7)))
