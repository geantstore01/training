from datetime import datetime, timedelta, timezone
from uuid import UUID
from pydantic import BaseModel
from sqlalchemy import select
from shared.db.models import MasteryRecord, LearningSession, ExerciseAttempt

class ProgressSummary(BaseModel):
    student_id: UUID
    competences_acquises: int
    competences_a_retravailler: int
    competences_en_apprentissage: int
    minutes_session_estimees: int
    tentatives_terminees: int
    message: str = "Chaque séance permet d'avancer à son rythme."

def minutes(intervals, start, end):
    spans = sorted((max(a,start), min(b,end,a+timedelta(minutes=30))) for a,b in intervals if b is not None and b>start and a<end)
    total, previous = 0.0, start
    for a,b in spans:
        if b > max(a, previous):
            total += (b-max(a,previous)).total_seconds()
        previous = max(previous,b)
    return int(total//60)

def summary(session, student_id, start, end):
    states = list(session.scalars(select(MasteryRecord.evaluation_level).where(MasteryRecord.student_id == student_id)))
    intervals = session.execute(select(LearningSession.started_at,LearningSession.ended_at).where(
        LearningSession.student_id == student_id, LearningSession.ended_at > start, LearningSession.started_at < end)).all()
    attempts = session.scalars(select(ExerciseAttempt.id).where(ExerciseAttempt.student_id == student_id,
        ExerciseAttempt.submitted_at >= start, ExerciseAttempt.submitted_at < end)).all()
    return ProgressSummary(student_id=student_id,competences_acquises=sum(x in {"maîtrisé","consolidé"} for x in states),
        competences_a_retravailler=states.count("fragile"),competences_en_apprentissage=sum(x in {"découverte","en_cours"} for x in states),
        minutes_session_estimees=minutes(intervals,start,end),tentatives_terminees=len(attempts))
