from datetime import datetime, timedelta, timezone
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select

from shared.db.models import SafetyEvent, School, Student
from shared.db.session import tenant_session
from shared.security.api import current_principal, enforce_rate
from shared.security.policy import accessible_student, consent_allowed
from shared.security.tokens import Principal
from .schemas import AnalyzeRequest, AnalyzeResponse

router = APIRouter(tags=["safety"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest, request: Request, principal: Principal = Depends(current_principal)):
    enforce_rate(request, "analyze", principal.user_id, 60)
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        school = session.get(School, principal.school_id)
        student_id = payload.student_id
        if student_id is None and principal.roles & {"parent", "teacher"} and not principal.roles & {"school_admin", "sys_admin", "content_creator", "student"}:
            raise HTTPException(422, "Le contexte élève est requis pour cette action.")
        if "student" in principal.roles:
            own = session.scalar(select(Student).where(Student.user_id == principal.user_id))
            if own is None or (student_id is not None and student_id != own.id):
                raise HTTPException(404, "Profil introuvable.")
            student_id = own.id
        names = []
        if student_id is not None:
            student = accessible_student(session, principal, student_id)
            # La modération locale protège aussi sans consentement ; seule une sortie transmissible est conditionnée.
            names.append(student.pseudonym)
            if student.identity_ciphertext is not None:
                identity = request.app.state.cipher.decrypt(student.identity_ciphertext,
                    school_id=principal.school_id, owner_id=student.id, purpose="student_identity")
                names += list(identity.values())
                names += [part for value in identity.values() for part in value.split() if len(part) >= 2]
            allowed = consent_allowed(session, student.id, "ai_local" if payload.destination == "local" else "ai_cloud")
        else:
            allowed = True
        try:
            result = request.app.state.safety.analyze(payload.text.get_secret_value(), names, [school.name])
        except Exception as exc:
            logging.getLogger("educapilote.safety").error("safety_engine_failure type=%s", type(exc).__name__)
            raise HTTPException(503, "Traitement de sécurité indisponible.") from None
        if not allowed and result.decision != "block":
            result.decision = "block"
            result.sanitized_text = None
            result.layers[-1].status = "block"
            result.layers[-1].codes.append("consent_required")
            result.message = "L'accord de ton représentant et ton accord sont nécessaires pour utiliser cette aide."
        expires = datetime.now(timezone.utc) + timedelta(days=request.app.state.settings.safety_retention_days)
        for layer in result.layers:
            if layer.status in {"block", "redact"}:
                session.add(SafetyEvent(tenant_id=principal.school_id, request_id=result.request_id,
                    student_id=student_id, layer=layer.layer, category=layer.name,
                    severity="high" if result.requires_adult_support else ("medium" if layer.status == "block" else "info"),
                    action="escalate" if result.requires_adult_support else layer.status,
                    rule_version=result.policy_version, expires_at=expires))
        return result
