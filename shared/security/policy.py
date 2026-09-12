from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import and_, exists, or_, select

from shared.db.models import (AuditLog, ConsentRecord, Enrollment, Guardian, GuardianStudent,
    Student, StudentAssent, Teacher, TeacherClass)

POLICY_VERSION = "2026-09-v1"
PURPOSES = {"ai_local", "ai_cloud", "voice"}


def student_query(principal):
    query = select(Student)
    if principal.roles & {"school_admin", "sys_admin"}:
        return query
    conditions = []
    if "student" in principal.roles:
        conditions.append(Student.user_id == principal.user_id)
    if "parent" in principal.roles:
        conditions.append(exists(select(GuardianStudent.id).join(Guardian,
            and_(Guardian.id == GuardianStudent.guardian_id, Guardian.tenant_id == GuardianStudent.tenant_id))
            .where(GuardianStudent.student_id == Student.id, Guardian.user_id == principal.user_id,
                GuardianStudent.revoked_at.is_(None), GuardianStudent.authority_verified_at.is_not(None), Guardian.verified_at.is_not(None))))
    if "teacher" in principal.roles:
        today = datetime.now(timezone.utc).date()
        conditions.append(exists(select(Enrollment.id).join(TeacherClass,
            and_(TeacherClass.class_id == Enrollment.class_id, TeacherClass.tenant_id == Enrollment.tenant_id))
            .join(Teacher, and_(Teacher.id == TeacherClass.teacher_id, Teacher.tenant_id == TeacherClass.tenant_id))
            .where(Enrollment.student_id == Student.id, Teacher.user_id == principal.user_id,
                Enrollment.starts_on <= today, or_(Enrollment.ends_on.is_(None), Enrollment.ends_on >= today))))
    if not conditions:
        raise HTTPException(403, "Accès aux profils élèves non autorisé.")
    return query.where(or_(*conditions))


def accessible_student(session, principal, student_id):
    student = session.scalar(student_query(principal).where(Student.id == student_id))
    if student is None:
        raise HTTPException(404, "Profil introuvable.")
    return student


def own_guardian(session, principal, student_id):
    guardian = session.scalar(select(Guardian).join(GuardianStudent,
        and_(GuardianStudent.guardian_id == Guardian.id, GuardianStudent.tenant_id == Guardian.tenant_id))
        .where(Guardian.user_id == principal.user_id, GuardianStudent.student_id == student_id,
            Guardian.verified_at.is_not(None), GuardianStudent.authority_verified_at.is_not(None), GuardianStudent.revoked_at.is_(None)))
    if guardian is None:
        raise HTTPException(403, "Lien parental vérifié requis.")
    return guardian


def consent_allowed(session, student_id, purpose):
    """Politique conservatrice : tous les représentants liés et l'élève doivent être d'accord."""
    now = datetime.now(timezone.utc)
    guardians = list(session.scalars(select(Guardian.id).join(GuardianStudent,
        and_(GuardianStudent.guardian_id == Guardian.id, GuardianStudent.tenant_id == Guardian.tenant_id))
        .where(GuardianStudent.student_id == student_id, GuardianStudent.revoked_at.is_(None),
            GuardianStudent.authority_verified_at.is_not(None), Guardian.verified_at.is_not(None))))
    if not guardians:
        return False
    for guardian in guardians:
        latest = session.scalar(select(ConsentRecord).where(ConsentRecord.student_id == student_id,
            ConsentRecord.guardian_id == guardian, ConsentRecord.purpose == purpose).order_by(ConsentRecord.revision.desc()).limit(1))
        if latest is None or not latest.granted or latest.withdrawn_at is not None or latest.policy_version != POLICY_VERSION or (latest.expires_at is not None and latest.expires_at <= now):
            return False
    assent = session.scalar(select(StudentAssent).where(StudentAssent.student_id == student_id,
        StudentAssent.purpose == purpose).order_by(StudentAssent.recorded_at.desc(), StudentAssent.id.desc()).limit(1))
    return assent is not None and assent.agreed and assent.policy_version == POLICY_VERSION


def audit(session, principal, action, resource_type, resource_id=None):
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    # INSERT sans RETURNING : le compte métier n'a pas de droit de lecture sur l'audit.
    session.add(AuditLog(id=uuid4(), created_at=now, updated_at=now, tenant_id=principal.school_id, actor_id=principal.user_id, action=action,
        resource_type=resource_type, resource_id=resource_id, correlation_id=uuid4(), outcome="success",
        expires_at=now + timedelta(days=90)))
