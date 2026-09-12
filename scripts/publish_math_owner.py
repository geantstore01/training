"""Publish the installed math pack by explicit owner request; no invented human reviews."""
from datetime import datetime,timezone
from types import SimpleNamespace
from uuid import UUID
from sqlalchemy import select
from shared.db.session import tenant_session
from shared.db.models import Lesson,LessonVersion,ExerciseVersion,ExerciseCompetency,LessonCompetency,Hint,ExerciseSource
from shared.exercises.cm2_pack import COURSES
from shared.exercises.schemas import Candidate
from shared.exercises.pipeline import validate
from shared.security.policy import audit

def publish(engine,tenant):
    actor=SimpleNamespace(school_id=tenant,user_id=None)
    published_exercises=0;published_lessons=0
    with tenant_session(engine,tenant) as session:
        codes=[c["code"] for c in COURSES if c["code"].startswith("CM2-MATH-")]
        assert len(codes)==32
        for code in codes:
            lesson=session.scalar(select(Lesson).where(Lesson.tenant_id==tenant,Lesson.slug==code.lower()))
            assert lesson,f"Leçon manquante : {code}"
            versions=session.scalars(select(LessonVersion).where(LessonVersion.tenant_id==tenant,LessonVersion.lesson_id==lesson.id).order_by(LessonVersion.version.desc())).all()
            version=next((v for v in versions if v.status in ('pending_review','approved') and (v.body or {}).get('cm2',{}).get('subject')=='mathematiques'),None)
            assert version,f"Version atelier mathématiques manquante : {code}"
            body=version.body['cm2'];assert body['subject']=='mathematiques'
            allowed=set(session.scalars(select(LessonCompetency.competency_id).where(LessonCompetency.tenant_id==tenant,LessonCompetency.lesson_version_id==version.id)))
            assert allowed
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
                    published_exercises+=1
            if version.status!='approved':
                for old in versions:
                    if old.id!=version.id and old.status=='approved':
                        audit(session,actor,'operator.owner_publication','lesson_version',old.id);session.flush()
                        old.status='archived';session.flush()
                audit(session,actor,'operator.owner_publication','lesson_version',version.id);session.flush()
                # published_at est posé par le trigger edu_guard_lesson_version lors de l'approbation.
                version.status='approved';session.flush()
                published_lessons+=1
    return {'lessons':32,'lessons_published':published_lessons,'exercises_published':published_exercises,'publication':'explicit_site_owner_request'}

if __name__=='__main__':
    import argparse,json
    from pathlib import Path
    from sqlalchemy import create_engine
    from shared.config import Settings
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--tenant',type=UUID,required=True);a=p.parse_args()
    engine=create_engine(Settings(db_user='postgres',db_password_file=Path('/run/secrets/postgres_password')).database_url())
    print(json.dumps(publish(engine,a.tenant)))
