"""Install enriched v2 bodies for the staged French workshops. Never approves content.

The exercises and their ids stay those of the published v1 pack; only the lesson
bodies (prerequisites, discovery, explanation, method, worked example, common
errors) are re-staged as a new version awaiting human review.
"""
import argparse
import json
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID
from sqlalchemy import create_engine, func, select
from shared.config import Settings
from shared.db.session import tenant_session
from shared.db.models import (Competency,Lesson,LessonCompetency,LessonSource,LessonVersion,Lesson,User)
from shared.security.policy import audit
from shared.exercises.cm2_pack import bind_lesson
from shared.exercises.french_deepening import enriched_courses


def stage(engine,tenant,owner,apply=False):
    operator=SimpleNamespace(school_id=tenant,user_id=None)
    entries=enriched_courses()
    with tenant_session(engine,tenant) as session:
        assert session.scalar(select(User.id).where(User.tenant_id==tenant,User.id==owner,User.status=="active"))
        created=0;unchanged=0;result=[]
        for entry in entries:
            slug=entry['code'].lower()+'-atelier-francais'
            lesson=session.scalar(select(Lesson).where(Lesson.tenant_id==tenant,Lesson.slug==slug))
            assert lesson,f"Leçon installée manquante : {entry['code']}"
            versions=session.scalars(select(LessonVersion).where(LessonVersion.tenant_id==tenant,LessonVersion.lesson_id==lesson.id).order_by(LessonVersion.version.desc())).all()
            reference=next((v for v in versions if v.status in ('pending_review','approved') and (v.body or {}).get('cm2',{}).get('subject')=='francais'),None)
            assert reference,f"Version française publiée manquante : {entry['code']}"
            competency_id=session.scalar(select(LessonCompetency.competency_id).where(LessonCompetency.tenant_id==tenant,LessonCompetency.lesson_version_id==reference.id))
            comp=session.scalar(select(Competency).where(Competency.id==competency_id))
            assert comp and comp.code==entry['code'],f"Compétence inattendue pour {entry['code']}"
            source_ids=list(session.scalars(select(LessonSource.source_id).where(LessonSource.tenant_id==tenant,LessonSource.lesson_version_id==reference.id)))
            assert source_ids,f"Source officielle manquante : {entry['code']}"
            body=reference.body['cm2'];assert body['subject']=='francais'
            exercise_ids=[UUID(body['check_exercise_id']),*[UUID(value) for value in body['practice_exercise_ids']]]
            assert len(set(exercise_ids))==3
            payload=bind_lesson(entry,dict(id=comp.id,code=comp.code,objectives=comp.objectives),source_ids,exercise_ids)
            if reference.body==payload['body']:
                unchanged+=1;result.append({'code':entry['code'],'lesson_id':str(lesson.id),'version':reference.version,'status':reference.status});continue
            if not apply:
                created+=1;continue
            number=(session.scalar(select(func.max(LessonVersion.version)).where(LessonVersion.tenant_id==tenant,LessonVersion.lesson_id==lesson.id)) or 0)+1
            version=LessonVersion(tenant_id=tenant,lesson_id=lesson.id,editor_id=None,version=number,title=entry['title'],body=payload['body'],status='draft');session.add(version);session.flush()
            session.add(LessonCompetency(tenant_id=tenant,lesson_version_id=version.id,competency_id=comp.id))
            session.add_all([LessonSource(tenant_id=tenant,lesson_version_id=version.id,source_id=value) for value in source_ids]);session.flush()
            version.status='pending_review';session.flush()
            audit(session,operator,'operator.french_lesson_staged','lesson_version',version.id)
            created+=1
            result.append({'code':entry['code'],'lesson_id':str(lesson.id),'version':version.version,'status':version.status})
        summary={'lessons':len(entries),'versions_created':created,'unchanged':unchanged,'publication':'human_review_required'}
        return {**summary,'courses':result} if apply else summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--tenant',type=UUID,required=True);p.add_argument('--owner',type=UUID,required=True);p.add_argument('--apply',action='store_true');a=p.parse_args()
    engine=create_engine(Settings(db_user='postgres',db_password_file=Path('/run/secrets/postgres_password')).database_url())
    print(json.dumps(stage(engine,a.tenant,a.owner,a.apply)))
