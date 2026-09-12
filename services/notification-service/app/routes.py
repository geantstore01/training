import hmac,json
from datetime import date,datetime,timezone
from typing import Literal
from uuid import UUID
from pathlib import Path
from fastapi import APIRouter,Depends,HTTPException,Request,Query
from pydantic import Field,model_validator
from redis.exceptions import RedisError
from sqlalchemy import select,text
from shared.ai.contracts import Strict
from shared.db.models import BackgroundJob,JobDispatch,Notification,Student
from shared.db.session import tenant_session
from shared.security.api import current_principal,subject_state,enforce_rate
from shared.security.tokens import Principal
from shared.security.policy import student_query
from shared.exercises.generation import GenerationInput

router=APIRouter()
ROLES={"weekly_reports":{"teacher","school_admin","sys_admin"},"difficulty_alerts":{"teacher","school_admin","sys_admin"},
    "exercise_batch":{"teacher","content_creator"},"privacy_purge":{"school_admin","sys_admin"}}
class JobInput(Strict):
    kind: Literal["weekly_reports","difficulty_alerts","exercise_batch","privacy_purge"]
    idempotency_key: UUID
    generations: list[GenerationInput]=Field(default_factory=list,max_length=10)
    @model_validator(mode="after")
    def shape(self):
        if (self.kind=="exercise_batch")!=bool(self.generations):raise ValueError("Générations requises uniquement pour les lots")
        return self
class JobView(Strict):
    id: UUID
    kind: str
    status: str
    attempts: int
    result: dict|None
    error_code: str|None
class Notice(Strict):
    id: UUID
    student_id: UUID
    kind: str
    period: date
    body: dict
    read_at: datetime|None

def job_view(row):return JobView(**{k:getattr(row,k) for k in JobView.model_fields})
def enqueue(body,request,p):
    if not p.roles & ROLES[body.kind]:raise HTTPException(403,"Tâche non autorisée.")
    payload={"generations":[g.model_dump(mode="json") for g in body.generations]}
    with tenant_session(request.app.state.engine,p.school_id) as s:
        s.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:k,0))"),{"k":f"job:{p.school_id}:{body.idempotency_key}"})
        row=s.scalar(select(BackgroundJob).where(BackgroundJob.idempotency_key==body.idempotency_key))
        if row:
            if row.kind!=body.kind or row.payload!=payload or row.requested_by!=p.user_id:raise HTTPException(409,"Clé déjà utilisée.")
        else:
            row=BackgroundJob(tenant_id=p.school_id,requested_by=p.user_id,kind=body.kind,idempotency_key=body.idempotency_key,payload=payload)
            s.add(row);s.flush();s.add(JobDispatch(school_id=p.school_id,job_id=row.id))
        result=job_view(row)
    try:request.app.state.cache.lpush("edu:jobs:wake",str(result.id))
    except RedisError:pass  # Enveloppe SQL durable : le worker la retrouvera par balayage.
    return result

@router.post("/jobs",response_model=JobView,status_code=202)
def create_job(body:JobInput,request:Request,p=Depends(current_principal)):
    enforce_rate(request,"jobs",p.user_id,20)
    return enqueue(body,request,p)

@router.get("/jobs/{id}",response_model=JobView)
def get_job(id:UUID,request:Request,p=Depends(current_principal)):
    with tenant_session(request.app.state.engine,p.school_id) as s:
        row=s.get(BackgroundJob,id)
        if not row or (row.requested_by!=p.user_id and not p.roles & {"school_admin","sys_admin"}):raise HTTPException(404,"Tâche introuvable.")
        return job_view(row)

@router.get("/inbox",response_model=list[Notice])
def inbox(request:Request,limit:int=Query(30,ge=1,le=100),p=Depends(current_principal)):
    with tenant_session(request.app.state.engine,p.school_id) as s:
        ids=student_query(p).with_only_columns(Student.id)
        rows=s.scalars(select(Notification).where(Notification.recipient_id==p.user_id,Notification.student_id.in_(ids),Notification.expires_at>datetime.now(timezone.utc)).order_by(Notification.created_at.desc()).limit(limit))
        return [Notice(**{k:getattr(x,k) for k in Notice.model_fields}) for x in rows]

@router.post("/inbox/{id}/read",response_model=Notice)
def read(id:UUID,request:Request,p=Depends(current_principal)):
    from shared.security.policy import accessible_student
    with tenant_session(request.app.state.engine,p.school_id) as s:
        row=s.scalar(select(Notification).where(Notification.id==id,Notification.recipient_id==p.user_id,Notification.expires_at>datetime.now(timezone.utc)))
        if not row:raise HTTPException(404,"Notification introuvable.")
        accessible_student(s,p,row.student_id);row.read_at=row.read_at or datetime.now(timezone.utc)
        return Notice(**{k:getattr(row,k) for k in Notice.model_fields})

@router.post("/automation/jobs",response_model=JobView,status_code=202)
def automation(body:JobInput,request:Request):
    from uuid import uuid4
    config=json.loads(request.app.state.settings.automation_keys_file.read_text())
    supplied=request.headers.get("X-Edu-Automation","")
    entry=next((v for v in config if hmac.compare_digest(supplied,v["token"])),None)
    if not entry or body.kind not in entry["kinds"]:raise HTTPException(403,"Intégration non autorisée.")
    school,user=UUID(entry["school_id"]),UUID(entry["user_id"])
    with tenant_session(request.app.state.engine,school) as s:state=subject_state(s,user)
    if not state:raise HTTPException(403,"Compte d'intégration inactif.")
    p=Principal(user_id=user,school_id=school,roles=state[1],auth_version=state[0],session_id=uuid4())
    enforce_rate(request,"automation",school,60)
    return enqueue(body,request,p)
