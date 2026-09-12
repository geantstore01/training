from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select

from shared.db.models import (ConsentRecord, CurriculumLevel, Guardian, GuardianStudent, School,
    Student, StudentAssent, Teacher, Tenant, User, UserRole)
from shared.db.session import tenant_session
from shared.security.api import current_principal, enforce_rate, require_roles
from shared.security.passwords import hash_password
from shared.security.policy import (POLICY_VERSION, PURPOSES, accessible_student, audit,
    consent_allowed, own_guardian, student_query)
from shared.security.tokens import Principal
from .schemas import (AccountInput, AccountUpdate, AccountView, AssentInput, AssentView,
    ConsentInput, ConsentPolicy, ConsentView, GuardianLinkInput, GuardianLinkView, Identity, Preferences,
    SchoolInput, SchoolView, StudentUpdate, StudentView, WithdrawalInput)

router = APIRouter(tags=["users"])
ADMIN = require_roles("school_admin", "sys_admin")
PARENT = require_roles("parent")


def account_view(session, user):
    return AccountView(id=user.id, school_id=user.tenant_id, login=user.login, status=user.status,
        roles=list(session.scalars(select(UserRole.role).where(UserRole.user_id == user.id))),
        student_id=session.scalar(select(Student.id).where(Student.user_id == user.id)),
        guardian_id=session.scalar(select(Guardian.id).where(Guardian.user_id == user.id)),
        teacher_id=session.scalar(select(Teacher.id).where(Teacher.user_id == user.id)))


def create_account(session, cipher, school_id, payload):
    user_id = uuid4()
    user = User(id=user_id, tenant_id=school_id, login=payload.login,
        password_hash=hash_password(payload.password.get_secret_value()), status="active")
    if payload.email:
        user.email_ciphertext = cipher.encrypt({"email": str(payload.email)}, school_id=school_id, owner_id=user_id, purpose="email")
    session.add(user)
    session.flush()
    session.add(UserRole(tenant_id=school_id, user_id=user_id, role=payload.role))
    if payload.role == "parent":
        session.add(Guardian(tenant_id=school_id, user_id=user_id))
    elif payload.role == "teacher":
        session.add(Teacher(tenant_id=school_id, user_id=user_id, display_name=payload.display_name))
    elif payload.role == "student":
        student_id = uuid4()
        identity = {"first_name": payload.student.first_name, "last_name": payload.student.last_name}
        level = session.scalar(select(CurriculumLevel.id).where(CurriculumLevel.code == payload.student.level))
        session.add(Student(id=student_id, tenant_id=school_id, user_id=user_id,
            pseudonym=payload.student.pseudonym, curriculum_level_id=level,
            identity_ciphertext=cipher.encrypt(identity, school_id=school_id, owner_id=student_id, purpose="student_identity")))
    session.flush()
    return account_view(session, user)


def student_view(session, student):
    return StudentView(id=student.id, user_id=student.user_id, school_id=student.tenant_id,
        pseudonym=student.pseudonym, level=session.scalar(select(CurriculumLevel.code).where(CurriculumLevel.id == student.curriculum_level_id)),
        accessibility_preferences=student.accessibility_preferences)


@router.get("/me", response_model=AccountView)
def me(request: Request, principal: Principal = Depends(current_principal)):
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        return account_view(session, session.get(User, principal.user_id))


@router.post("/accounts", status_code=201, response_model=AccountView)
def add_account(payload: AccountInput, request: Request, principal: Principal = Depends(ADMIN)):
    if payload.role == "sys_admin" or (payload.role == "school_admin" and "sys_admin" not in principal.roles):
        raise HTTPException(403, "Attribution de ce rôle non autorisée.")
    enforce_rate(request, "create-account", principal.user_id, 30)
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        result = create_account(session, request.app.state.cipher, principal.school_id, payload)
        audit(session, principal, "user.created", "user", result.id)
        return result


@router.get("/accounts", response_model=list[AccountView])
def accounts(request: Request, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0, le=10000), principal: Principal = Depends(ADMIN)):
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        return [account_view(session, u) for u in session.scalars(select(User).order_by(User.id).limit(limit).offset(offset))]


@router.patch("/accounts/{user_id}", response_model=AccountView)
def update_account(user_id: UUID, payload: AccountUpdate, request: Request, principal: Principal = Depends(ADMIN)):
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        user = session.scalar(select(User).where(User.id == user_id).with_for_update())
        if user is None:
            raise HTTPException(404, "Compte introuvable.")
        roles = set(session.scalars(select(UserRole.role).where(UserRole.user_id == user_id)))
        if user_id == principal.user_id or "sys_admin" in roles or ("school_admin" in roles and "sys_admin" not in principal.roles):
            raise HTTPException(403, "Modification de ce compte non autorisée.")
        if payload.status is None and payload.password is None:
            raise HTTPException(422, "Modification vide.")
        if payload.status:
            user.status = payload.status
        if payload.password:
            enforce_rate(request, "reset-password", principal.user_id, 10)
            user.password_hash = hash_password(payload.password.get_secret_value())
        user.auth_version += 1
        audit(session, principal, "user.access_updated", "user", user.id)
        session.flush()
        return account_view(session, user)


@router.post("/schools", status_code=201, response_model=SchoolView)
def create_school(payload: SchoolInput, request: Request, principal: Principal = Depends(require_roles("sys_admin"))):
    enforce_rate(request, "create-school", principal.user_id, 5)
    school_id = uuid4()
    # Une transaction SQL unique ; le changement de contexte est réservé à cette route sys_admin.
    with tenant_session(request.app.state.engine, school_id) as session:
        session.add(Tenant(id=school_id, name=payload.name))
        session.flush()
        session.add(School(id=school_id, tenant_id=school_id, name=payload.name))
        session.flush()
        account = create_account(session, request.app.state.cipher, school_id, payload.admin)
        from sqlalchemy import text
        session.execute(text("SELECT set_config('app.tenant_id', :school, true)"), {"school": str(principal.school_id)})
        audit(session, principal, "school.created", "school", school_id)
        return SchoolView(school_id=school_id, name=payload.name, administrator=account)


@router.get("/students", response_model=list[StudentView])
def students(request: Request, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0, le=10000), principal: Principal = Depends(current_principal)):
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        return [student_view(session, s) for s in session.scalars(student_query(principal).order_by(Student.id).limit(limit).offset(offset))]


@router.get("/students/{student_id}", response_model=StudentView)
def get_student(student_id: UUID, request: Request, principal: Principal = Depends(current_principal)):
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        return student_view(session, accessible_student(session, principal, student_id))


@router.get("/students/{student_id}/identity", response_model=Identity)
def get_identity(student_id: UUID, request: Request, principal: Principal = Depends(current_principal)):
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        student = accessible_student(session, principal, student_id)
        if student.identity_ciphertext is None:
            raise HTTPException(404, "Identité non renseignée.")
        identity = request.app.state.cipher.decrypt(student.identity_ciphertext, school_id=principal.school_id, owner_id=student.id, purpose="student_identity")
        audit(session, principal, "student.identity_read", "student", student.id)
        return Identity(**identity)


@router.patch("/students/{student_id}", response_model=StudentView)
def update_student(student_id: UUID, payload: StudentUpdate, request: Request, principal: Principal = Depends(ADMIN)):
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        student = accessible_student(session, principal, student_id)
        if payload.pseudonym is not None:
            student.pseudonym = payload.pseudonym
        if payload.level is not None:
            student.curriculum_level_id = session.scalar(select(CurriculumLevel.id).where(CurriculumLevel.code == payload.level))
        if payload.identity is not None:
            student.identity_ciphertext = request.app.state.cipher.encrypt(payload.identity.model_dump(), school_id=principal.school_id, owner_id=student.id, purpose="student_identity")
        audit(session, principal, "student.updated", "student", student.id)
        session.flush()
        return student_view(session, student)


@router.put("/students/{student_id}/preferences", response_model=StudentView)
def preferences(student_id: UUID, payload: Preferences, request: Request, principal: Principal = Depends(current_principal)):
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        student = accessible_student(session, principal, student_id)
        student.accessibility_preferences = payload.model_dump()
        audit(session, principal, "student.preferences_updated", "student", student.id)
        session.flush()
        return student_view(session, student)


@router.post("/guardian-links", status_code=201, response_model=GuardianLinkView)
def link_guardian(payload: GuardianLinkInput, request: Request, principal: Principal = Depends(ADMIN)):
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        accessible_student(session, principal, payload.student_id)
        guardian = session.get(Guardian, payload.guardian_id)
        if guardian is None:
            raise HTTPException(404, "Représentant introuvable.")
        now, link_id = datetime.now(timezone.utc), uuid4()
        if guardian.verified_at is None:
            guardian.verified_at = now
        link = GuardianStudent(id=link_id, tenant_id=principal.school_id, student_id=payload.student_id,
            guardian_id=payload.guardian_id, relationship=payload.relationship,
            authority_verified_at=now, verified_by=principal.user_id,
            verification_evidence_ciphertext=request.app.state.cipher.encrypt(
                {"reference": payload.verification_reference.get_secret_value(), "verified_by": str(principal.user_id)},
                school_id=principal.school_id, owner_id=link_id, purpose="guardian_verification"))
        session.add(link)
        audit(session, principal, "guardian.link_verified", "guardian_link", link_id)
        session.flush()
        return GuardianLinkView.model_validate(link)


@router.post("/guardian-links/{link_id}/revoke", response_model=GuardianLinkView)
def revoke_link(link_id: UUID, request: Request, principal: Principal = Depends(ADMIN)):
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        link = session.scalar(select(GuardianStudent).where(GuardianStudent.id == link_id).with_for_update())
        if link is None:
            raise HTTPException(404, "Lien introuvable.")
        if link.revoked_at is not None:
            return GuardianLinkView.model_validate(link)
        link.revoked_at = datetime.now(timezone.utc)
        audit(session, principal, "guardian.link_revoked", "guardian_link", link.id)
        session.flush()
        return GuardianLinkView.model_validate(link)


@router.get("/consent-policy", response_model=ConsentPolicy)
def consent_policy():
    return {"version": POLICY_VERSION, "purposes": {
        "ai_local": "Recevoir une aide pédagogique d'une IA exécutée sur le serveur de l'école.",
        "ai_cloud": "Autoriser une aide IA externe après filtrage des informations personnelles.",
        "voice": "Utiliser les fonctions vocales pour lire ou dicter des consignes."},
        "child_notice": "Tu peux dire oui ou non à ces aides. Tu peux changer d'avis. Demande à un adulte si tu ne comprends pas.",
        "withdrawal": "Le parent et l'élève peuvent retirer leur accord dans leur espace. Les cours sans ces options restent distincts."}


def policy_check(version):
    if version != POLICY_VERSION:
        raise HTTPException(409, "Consulte la version actuelle de la notice.")


def append_consent(session, request, principal, student_id, purpose, version, event, understood):
    policy_check(version)
    accessible_student(session, principal, student_id)
    guardian = own_guardian(session, principal, student_id)
    if event == "withdraw":
        previous = session.scalar(select(ConsentRecord).where(ConsentRecord.student_id == student_id,
            ConsentRecord.guardian_id == guardian.id, ConsentRecord.purpose == purpose).order_by(ConsentRecord.revision.desc()).limit(1))
        if previous is None or not previous.granted or previous.withdrawn_at is not None:
            raise HTTPException(409, "Aucun accord actif à retirer.")
    record_id = uuid4()
    proof = {"actor": str(principal.user_id), "session": str(principal.session_id), "policy_version": version,
        "purpose": purpose, "event": event, "understood": understood, "received_at": datetime.now(timezone.utc).isoformat()}
    record = ConsentRecord(id=record_id, tenant_id=principal.school_id, student_id=student_id,
        guardian_id=guardian.id, recorded_by=principal.user_id, purpose=purpose, policy_version=version,
        legal_basis="consent", granted=event == "grant", event_type=event,
        evidence_ciphertext=request.app.state.cipher.encrypt(proof, school_id=principal.school_id, owner_id=record_id, purpose="consent_evidence"))
    session.add(record)
    session.flush()
    session.refresh(record)
    audit(session, principal, f"consent.{event}", "consent", record_id)
    return ConsentView.model_validate(record)


@router.post("/students/{student_id}/consents", status_code=201, response_model=ConsentView)
def grant_consent(student_id: UUID, payload: ConsentInput, request: Request, principal: Principal = Depends(PARENT)):
    enforce_rate(request, "consent", principal.user_id, 30)
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        return append_consent(session, request, principal, student_id, payload.purpose, payload.policy_version,
            "grant" if payload.granted else "refuse", payload.understood)


@router.post("/students/{student_id}/consents/withdraw", status_code=201, response_model=ConsentView)
def withdraw_consent(student_id: UUID, payload: WithdrawalInput, request: Request, principal: Principal = Depends(PARENT)):
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        return append_consent(session, request, principal, student_id, payload.purpose, payload.policy_version, "withdraw", False)


@router.get("/students/{student_id}/consents", response_model=list[ConsentView])
def consent_history(student_id: UUID, request: Request, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0, le=10000),
    principal: Principal = Depends(require_roles("parent", "student", "school_admin", "sys_admin"))):
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        accessible_student(session, principal, student_id)
        query = select(ConsentRecord).where(ConsentRecord.student_id == student_id)
        if "parent" in principal.roles and not principal.roles & {"school_admin", "sys_admin"}:
            query = query.where(ConsentRecord.guardian_id == own_guardian(session, principal, student_id).id)
        return [ConsentView.model_validate(c) for c in session.scalars(query.order_by(ConsentRecord.recorded_at.desc(), ConsentRecord.id.desc()).limit(limit).offset(offset))]


@router.post("/me/assents", status_code=201, response_model=AssentView)
def record_assent(payload: AssentInput, request: Request, principal: Principal = Depends(require_roles("student"))):
    policy_check(payload.policy_version)
    enforce_rate(request, "assent", principal.user_id, 30)
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        student = session.scalar(select(Student).where(Student.user_id == principal.user_id))
        if student is None:
            raise HTTPException(404, "Profil introuvable.")
        record = StudentAssent(tenant_id=principal.school_id, student_id=student.id,
            recorded_by=principal.user_id, purpose=payload.purpose, policy_version=payload.policy_version, agreed=payload.agreed)
        session.add(record)
        session.flush()
        audit(session, principal, "student.assent_recorded", "student_assent", record.id)
        return AssentView.model_validate(record)


@router.get("/students/{student_id}/permissions", response_model=dict[str, bool])
def permissions(student_id: UUID, request: Request, principal: Principal = Depends(current_principal)):
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        accessible_student(session, principal, student_id)
        return {purpose: consent_allowed(session, student_id, purpose) for purpose in sorted(PURPOSES)}
