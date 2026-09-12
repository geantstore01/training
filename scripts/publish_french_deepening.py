"""Publish the enriched French lesson versions by explicit owner request; no invented reviews.

Exercises are untouched (already published by publish_french_owner); publishing a
new lesson version archives the previously approved one so each lesson keeps
exactly one approved version (constraint uq_lesson_one_approved). published_at is
set by the trigger edu_guard_lesson_version, never by this script.
"""
import argparse
import json
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID
from sqlalchemy import create_engine, select
from shared.config import Settings
from shared.db.session import tenant_session
from shared.db.models import ExerciseVersion,Lesson,LessonVersion
from shared.security.policy import audit
from shared.exercises.french_deepening import enriched_courses


def publish(engine,tenant):
    actor=SimpleNamespace(school_id=tenant,user_id=None)
    published=0
    with tenant_session(engine,tenant) as session:
        for entry in enriched_courses():
            slug=entry['code'].lower()+'-atelier-francais'
            lesson=session.scalar(select(Lesson).where(Lesson.tenant_id==tenant,Lesson.slug==slug))
            assert lesson,f"Leçon installée manquante : {entry['code']}"
            versions=session.scalars(select(LessonVersion).where(LessonVersion.tenant_id==tenant,LessonVersion.lesson_id==lesson.id).order_by(LessonVersion.version.desc())).all()
            version=next((v for v in versions if v.status in ('pending_review','approved') and (v.body or {}).get('cm2',{}).get('subject')=='francais'),None)
            assert version,f"Version française enrichie manquante : {entry['code']}"
            body=version.body['cm2'];assert body['subject']=='francais'
            ids={UUID(body['check_exercise_id']),*[UUID(value) for value in body['practice_exercise_ids']]}
            assert len(ids)==3,f"Identifiants d'exercices incohérents : {entry['code']}"
            for identifier in ids:
                exercise=session.scalar(select(ExerciseVersion).where(ExerciseVersion.tenant_id==tenant,ExerciseVersion.id==identifier))
                assert exercise and exercise.status=='published',f"Exercice non publié : {identifier}"
            if version.status=='approved':continue
            for old in versions:
                if old.id!=version.id and old.status=='approved':
                    audit(session,actor,'operator.owner_publication','lesson_version',old.id);session.flush()
                    old.status='archived';session.flush()
            audit(session,actor,'operator.owner_publication','lesson_version',version.id);session.flush()
            version.status='approved';session.flush()
            published+=1
    return {'lessons':28,'lessons_published':published,'publication':'explicit_site_owner_request'}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--tenant',type=UUID,required=True);a=p.parse_args()
    engine=create_engine(Settings(db_user='postgres',db_password_file=Path('/run/secrets/postgres_password')).database_url())
    print(json.dumps(publish(engine,a.tenant)))
