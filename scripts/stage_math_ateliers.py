"""Install the 32 authored math workshops for human review. Never approves content."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID
from sqlalchemy import create_engine, func, select
from shared.config import Settings
from shared.db.session import tenant_session
from shared.db.models import (Competency,ContentSource,Exercise,ExerciseVersion,ExerciseCompetency,ExerciseSource,
    Hint,Lesson,LessonVersion,LessonCompetency,LessonSource,User)
from shared.security.policy import audit
from shared.exercises.cm2_pack import COURSES,bind_exercises,bind_lesson
from shared.exercises.schemas import PublicPrompt
from shared.exercises.pipeline import validate
from shared.exercises.correctors import VERSION

SOURCE_URL="https://www.education.gouv.fr/sites/default/files/programme-de-math-matiques-pour-le-cycle-3-439827.pdf"

def stage(engine,tenant,owner,source_file,apply=False):
    raw=source_file.read_bytes()
    if not raw.startswith(b"%PDF"):raise ValueError("PDF officiel requis")
    digest=hashlib.sha256(raw).hexdigest()
    operator=SimpleNamespace(school_id=tenant,user_id=None)
    math_courses=[c for c in COURSES if c["code"].startswith("CM2-MATH-")]
    with tenant_session(engine,tenant) as session:
        assert session.scalar(select(User.id).where(User.tenant_id==tenant,User.id==owner,User.status=="active"))
        comps={c.code:c for c in session.scalars(select(Competency).where(Competency.programme_version=="programme-2025-cm2-2026",Competency.code.in_([c['code'] for c in math_courses])))}
        assert len(comps)==len(math_courses)==32
        if not apply:return {"courses":32,"exercises":96,"source_sha256":digest,"publication":"human_review_required"}
        source=session.scalar(select(ContentSource).where(ContentSource.tenant_id==tenant,ContentSource.url==SOURCE_URL,ContentSource.checksum_sha256==digest))
        if not source:
            source=ContentSource(tenant_id=tenant,title="Programme de mathématiques du cycle 3 — CM2, rentrée 2026",url=SOURCE_URL,publisher="Ministère de l’Éducation nationale",license="Référence officielle ; cours et exercices originaux BoostClasse.",checksum_sha256=digest,retrieved_at=datetime.now(timezone.utc))
            session.add(source);session.flush()
        created=0;result=[]
        for entry in math_courses:
            comp=comps[entry['code']];ids=[]
            for index,candidate in enumerate(bind_exercises(entry,comp.id,[source.id])):
                slug=entry['code'].lower()+f'-atelier-math-{index}'
                item=session.scalar(select(Exercise).where(Exercise.tenant_id==tenant,Exercise.slug==slug))
                if item:
                    version=session.scalar(select(ExerciseVersion).where(ExerciseVersion.tenant_id==tenant,ExerciseVersion.exercise_id==item.id,ExerciseVersion.version==1))
                    assert version
                else:
                    report=validate(candidate,{comp.id},{source.id});assert report.passed
                    item=Exercise(tenant_id=tenant,slug=slug,author_id=owner);session.add(item);session.flush()
                    version=ExerciseVersion(tenant_id=tenant,exercise_id=item.id,version=1,kind=candidate.kind,prompt=PublicPrompt(instruction=candidate.instruction,parts=candidate.parts).model_dump(mode='json'),answer_spec={k:r.model_dump(mode='json') for k,r in candidate.answers.items()},validator_name='controlled',validator_version=VERSION,difficulty=candidate.difficulty,pipeline_report=[x.model_dump() for x in report.checks],status='draft')
                    session.add(version);session.flush()
                    session.add(ExerciseCompetency(tenant_id=tenant,exercise_version_id=version.id,competency_id=comp.id,weight=1))
                    session.add(ExerciseSource(tenant_id=tenant,exercise_version_id=version.id,source_id=source.id))
                    session.add_all([Hint(tenant_id=tenant,exercise_version_id=version.id,level=h.level,body={'text':h.text}) for h in candidate.hints]);session.flush()
                    version.status='in_review';session.flush()
                    audit(session,operator,'operator.math_exercise_staged','exercise_version',version.id);created+=1
                ids.append(version.id)
            payload=bind_lesson(entry,dict(id=comp.id,code=comp.code,objectives=comp.objectives),[source.id],ids)
            slug=entry['code'].lower()
            lesson=session.scalar(select(Lesson).where(Lesson.tenant_id==tenant,Lesson.slug==slug))
            if not lesson:
                lesson=Lesson(tenant_id=tenant,slug=slug,kind='lesson',author_id=owner);session.add(lesson);session.flush()
            version=session.scalar(select(LessonVersion).where(LessonVersion.tenant_id==tenant,LessonVersion.lesson_id==lesson.id,LessonVersion.status.in_(('pending_review','approved')),LessonVersion.body['cm2']['subject'].astext=='mathematiques'))
            if not version:
                number=(session.scalar(select(func.max(LessonVersion.version)).where(LessonVersion.tenant_id==tenant,LessonVersion.lesson_id==lesson.id)) or 0)+1
                version=LessonVersion(tenant_id=tenant,lesson_id=lesson.id,editor_id=None,version=number,title=entry['title'],body=payload['body'],status='draft');session.add(version);session.flush()
                session.add(LessonCompetency(tenant_id=tenant,lesson_version_id=version.id,competency_id=comp.id));session.add(LessonSource(tenant_id=tenant,lesson_version_id=version.id,source_id=source.id));session.flush()
                version.status='pending_review';session.flush()
                audit(session,operator,'operator.math_lesson_staged','lesson_version',version.id)
            result.append({'code':entry['code'],'lesson_id':str(lesson.id),'version':version.version,'status':version.status})
        return {'courses':result,'exercises_created':created,'publication':'human_review_required'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--tenant',type=UUID,required=True);p.add_argument('--owner',type=UUID,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--apply',action='store_true');a=p.parse_args()
    engine=create_engine(Settings(db_user='postgres',db_password_file=Path('/run/secrets/postgres_password')).database_url())
    print(json.dumps(stage(engine,a.tenant,a.owner,a.source,a.apply)))
