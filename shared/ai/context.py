from datetime import date
from fastapi import HTTPException
from sqlalchemy import or_, select
from shared.db.models import (Student, ExerciseAttempt, LearningSession, Competency,
    ExerciseCompetency, Subject, CurriculumLevel, RagDocument, RagPassage)

def attempt_context(session, principal, id, *, include_submitted=False):
    if "student" not in principal.roles:
        raise HTTPException(403, "Espace élève requis.")
    row = session.execute(select(ExerciseAttempt, Student.curriculum_level_id)
        .join(Student, Student.id == ExerciseAttempt.student_id)
        .join(LearningSession, LearningSession.id == ExerciseAttempt.session_id)
        .where(ExerciseAttempt.id == id, Student.user_id == principal.user_id,
            LearningSession.status == "active",
            *([] if include_submitted else [ExerciseAttempt.submitted_at.is_(None)]))).one_or_none()
    if row is None:
        raise HTTPException(404, "Tentative active introuvable.")
    attempt, level_id = row
    from shared.school import tutor_limit
    tutor_limit(session, attempt.student_id)
    skills = session.execute(select(Competency.label, Subject.code, CurriculumLevel.code)
        .join(Subject, Subject.id == Competency.subject_id).join(CurriculumLevel, CurriculumLevel.id == Competency.curriculum_level_id)
        .join(ExerciseCompetency, ExerciseCompetency.competency_id == Competency.id)
        .where(ExerciseCompetency.exercise_version_id == attempt.exercise_version_id,
            Competency.curriculum_level_id == level_id).order_by(Competency.id)).all()
    if not skills or len({x[1] for x in skills}) != 1:
        raise HTTPException(409, "Compétences compatibles avec le niveau requises.")
    return attempt, skills[0][2], skills[0][1], " ".join(x[0] for x in skills)[:450]

def passages(session, ids, level, subject, model):
    return session.execute(select(RagPassage.id, RagPassage.body).join(RagDocument, RagDocument.id == RagPassage.document_id)
        .where(RagPassage.id.in_(ids), RagDocument.status == "approved", RagDocument.level == level,
            RagDocument.subject == subject, RagDocument.effective_from <= date.today(),
            or_(RagDocument.effective_until.is_(None), RagDocument.effective_until >= date.today()), RagPassage.embedding_model == model)).all()
