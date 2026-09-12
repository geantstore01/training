from datetime import date
from fastapi import HTTPException
from sqlalchemy import exists, or_, select
from shared.db.models import Class, Teacher, TeacherClass, Enrollment, FeatureFlag

def flag(session, key):
    value = session.scalar(select(FeatureFlag.enabled).where(FeatureFlag.key == key))
    if value is False:
        raise HTTPException(403, "Fonction désactivée pour cet établissement.")

def class_access(session, principal, identifier):
    query = select(Class).where(Class.id == identifier)
    if not principal.roles & {"school_admin", "sys_admin"}:
        if "teacher" not in principal.roles:
            raise HTTPException(403, "Espace enseignant requis.")
        query = query.where(exists(select(TeacherClass.id).join(Teacher, Teacher.id == TeacherClass.teacher_id)
            .where(TeacherClass.class_id == Class.id, Teacher.user_id == principal.user_id)))
    row = session.scalar(query)
    if row is None:
        raise HTTPException(404, "Classe introuvable.")
    return row

def active_enrollment(student_id, class_id):
    return select(Enrollment).where(Enrollment.student_id == student_id, Enrollment.class_id == class_id,
        Enrollment.starts_on <= date.today(), or_(Enrollment.ends_on.is_(None), Enrollment.ends_on >= date.today()))


def tutor_limit(session, student_id):
    from shared.db.models import TutorControl
    row=session.scalar(select(TutorControl).where(TutorControl.student_id==student_id))
    if row and not row.enabled:raise HTTPException(403,"Accompagnement IA suspendu par l'enseignant.")
    return row.max_help if row else 6
