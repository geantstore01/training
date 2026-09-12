from datetime import datetime,timedelta,timezone
from collections import Counter
from decimal import Decimal
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import select,delete,func
from shared.db.models import (Notification,Guardian,GuardianStudent,Teacher,TeacherClass,Enrollment,Student,ExerciseAttempt,
    Exercise,ExerciseVersion,ExerciseCompetency,ExerciseSource,Hint,Competency,ContentSource,Subject,SafetyEvent,AIInteraction,AuditLog,TutorTurn,BackgroundJob)
from shared.security.policy import student_query
from shared.progression import summary
from shared.school import flag
from shared.exercises.generation import GenerationInput,generate
from shared.exercises.pipeline import validate
from shared.exercises.schemas import PublicPrompt
from shared.exercises.correctors import VERSION

def run_job(s,p,job):
    now=datetime.now(timezone.utc)
    if job.kind=="privacy_purge":
        counts={}
        from shared.db.models import ScienceRun
        for model in [Notification,TutorTurn,SafetyEvent,AIInteraction,AuditLog,ScienceRun]:
            statement=delete(model).where(model.expires_at<=now)
            if model is AIInteraction:
                statement=statement.where(~select(SafetyEvent.id).where(SafetyEvent.interaction_id==AIInteraction.id,SafetyEvent.tenant_id==AIInteraction.tenant_id).exists())
            counts[model.__tablename__]=s.execute(statement).rowcount
        counts["background_jobs"]=s.execute(delete(BackgroundJob).where(BackgroundJob.id!=job.id,BackgroundJob.status!="queued",BackgroundJob.created_at<now-timedelta(days=30))).rowcount
        return counts
    if job.kind=="exercise_batch":
        ids=[]
        for raw in job.payload["generations"]:
            g=GenerationInput.model_validate(raw)
            code=s.scalar(select(Subject.code).join(Competency,Competency.subject_id==Subject.id).where(Competency.id==g.competency_id))
            if code!={"arithmetic":"mathematiques","agreement":"francais","chronology":"histoire"}[g.template]:raise ValueError("generation_scope")
            c=generate(g)
            report=validate(c,set(s.scalars(select(Competency.id).where(Competency.id.in_([part.competency_id for part in c.parts])))),
                set(s.scalars(select(ContentSource.id).where(ContentSource.id.in_(c.source_ids)))))
            if not report.passed:raise ValueError("generation_validation")
            item=Exercise(tenant_id=p.school_id,author_id=p.user_id,slug="batch-"+uuid4().hex);s.add(item);s.flush()
            v=ExerciseVersion(tenant_id=p.school_id,exercise_id=item.id,version=1,kind=c.kind,status="draft",
                prompt=PublicPrompt(instruction=c.instruction,parts=c.parts).model_dump(mode="json"),answer_spec={k:r.model_dump(mode="json") for k,r in c.answers.items()},
                validator_name="controlled",validator_version=VERSION,difficulty=c.difficulty,pipeline_report=[x.model_dump() for x in report.checks]);s.add(v);s.flush()
            counts=Counter(part.competency_id for part in c.parts)
            s.add_all([ExerciseCompetency(tenant_id=p.school_id,exercise_version_id=v.id,competency_id=k,weight=Decimal(n)/len(c.parts)) for k,n in counts.items()])
            s.add_all([ExerciseSource(tenant_id=p.school_id,exercise_version_id=v.id,source_id=x) for x in c.source_ids])
            s.add_all([Hint(tenant_id=p.school_id,exercise_version_id=v.id,level=h.level,body={"text":h.text}) for h in c.hints])
            ids.append(str(v.id))
        return {"draft_version_ids":ids}
    flag(s,"notifications")
    end=datetime.combine(now.date()-timedelta(days=now.weekday()),datetime.min.time(),tzinfo=timezone.utc)
    start=end-timedelta(days=7)
    kind="weekly_report" if job.kind=="weekly_reports" else "difficulty_alert"
    if kind=="difficulty_alert":start=now-timedelta(days=7);end=now
    delivered=0
    students=s.scalars(student_query(p).limit(1001)).all()
    if len(students)>1000:raise ValueError("school_batch_limit")
    for student in students:
        if kind=="weekly_report":
            recipients=s.scalars(select(Guardian.user_id).join(GuardianStudent,GuardianStudent.guardian_id==Guardian.id).where(
                GuardianStudent.student_id==student.id,Guardian.verified_at.is_not(None),GuardianStudent.authority_verified_at.is_not(None),GuardianStudent.revoked_at.is_(None))).all()
            body=summary(s,student.id,start,end).model_dump(mode="json")
        else:
            count=s.scalar(select(func.count()).select_from(ExerciseAttempt).where(ExerciseAttempt.student_id==student.id,
                ExerciseAttempt.submitted_at>=start,ExerciseAttempt.score<Decimal("0.5")))
            helped=s.scalar(select(func.count()).select_from(ExerciseAttempt).where(ExerciseAttempt.student_id==student.id,
                ExerciseAttempt.started_at>=start,ExerciseAttempt.max_hint_level>=5))
            if count<3 and helped<2:continue
            recipients=s.scalars(select(Teacher.user_id).join(TeacherClass,TeacherClass.teacher_id==Teacher.id).join(Enrollment,Enrollment.class_id==TeacherClass.class_id)
                .where(Enrollment.student_id==student.id,Enrollment.starts_on<=now.date(),(Enrollment.ends_on.is_(None))|(Enrollment.ends_on>=now.date()))).all()
            body={"message":"Plusieurs essais suggèrent qu'un accompagnement serait utile.","action":"proposer_un_echange"}
        period=start.date() if kind=="weekly_report" else now.date()
        for recipient in set(recipients):
            if s.scalar(select(Notification.id).where(Notification.recipient_id==recipient,Notification.student_id==student.id,Notification.kind==kind,Notification.period==period)):continue
            s.add(Notification(tenant_id=p.school_id,recipient_id=recipient,student_id=student.id,kind=kind,period=period,body=body,expires_at=now+timedelta(days=30)))
            delivered+=1
    return {"notifications_created":delivered,"channel":"in_app"}
