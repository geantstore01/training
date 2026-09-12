"""Publish the installed French pack by explicit owner request; no invented human reviews."""
from datetime import datetime,timezone
from types import SimpleNamespace
from uuid import UUID
from sqlalchemy import select
from shared.db.session import tenant_session
from shared.db.models import Lesson,LessonVersion,Exercise,ExerciseVersion,ExerciseCompetency,LessonCompetency,Hint,ExerciseSource
from shared.exercises.schemas import Candidate
from shared.exercises.pipeline import validate
from shared.security.policy import audit

def publish(engine,tenant):
    actor=SimpleNamespace(school_id=tenant,user_id=None)
    with tenant_session(engine,tenant) as session:
        lessons=session.execute(select(Lesson,LessonVersion).join(LessonVersion,LessonVersion.lesson_id==Lesson.id).where(Lesson.tenant_id==tenant,LessonVersion.tenant_id==tenant,Lesson.slug.like('cm2-fr-%-atelier-francais'),LessonVersion.version==1)).all()
        assert len(lessons)==28
        for lesson,version in lessons:
            if version.status=='approved':continue
            assert version.status=='pending_review'
            body=version.body['cm2'];assert body['subject']=='francais'
            allowed=set(session.scalars(select(LessonCompetency.competency_id).where(LessonCompetency.tenant_id==tenant,LessonCompetency.lesson_version_id==version.id)))
            ids=[UUID(body['check_exercise_id']),*[UUID(x) for x in body['practice_exercise_ids']]]
            assert len(set(ids))==3
            for identifier in ids:
                ex=session.scalar(select(ExerciseVersion).where(ExerciseVersion.tenant_id==tenant,ExerciseVersion.id==identifier))
                assert ex and ex.status in ('in_review','published')
                sources=list(session.scalars(select(ExerciseSource.source_id).where(ExerciseSource.tenant_id==tenant,ExerciseSource.exercise_version_id==ex.id)))
                hints=[dict(level=h.level,text=h.body['text']) for h in session.scalars(select(Hint).where(Hint.tenant_id==tenant,Hint.exercise_version_id==ex.id))]
                c=Candidate(kind=ex.kind,instruction=ex.prompt['instruction'],parts=ex.prompt['parts'],answers=ex.answer_spec,source_ids=sources,difficulty=ex.difficulty,hints=hints)
                assert validate(c,allowed,set(sources)).passed
                if ex.status!='published':
                    audit(session,actor,'operator.owner_publication','exercise_version',ex.id);session.flush()
                    ex.status='published';ex.published_at=datetime.now(timezone.utc);session.flush()
            audit(session,actor,'operator.owner_publication','lesson_version',version.id);session.flush()
            version.status='approved';session.flush()
    return {'lessons':28,'exercises':84,'publication':'explicit_site_owner_request'}
