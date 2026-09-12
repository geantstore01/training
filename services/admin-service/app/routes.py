from datetime import datetime
from typing import Literal
from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException,Request,Query
from pydantic import Field
from sqlalchemy import select,text
from shared.ai.contracts import Strict
from shared.db.models import FeatureFlag,SafetyEvent,SafetyCase,LessonVersion,ExerciseVersion,RagDocument
from shared.db.session import tenant_session
from shared.security.api import require_roles
from shared.security.policy import audit

router=APIRouter()
admin=require_roles("school_admin","sys_admin")

class FlagInput(Strict):
    enabled: bool
    expected_revision: int=Field(ge=0)
class FlagView(Strict):
    key: str
    enabled: bool
    revision: int
class EventView(Strict):
    id: UUID
    student_id: UUID|None
    category: str
    severity: str
    action: str
    created_at: datetime
class CaseInput(Strict):
    resolution: Literal["reviewed","escalated","false_positive"]
class CaseView(CaseInput):
    id: UUID
class Pending(Strict):
    kind: Literal["lesson","exercise","rag"]
    id: UUID
    content_id: UUID
    version: int
    review_path: str

@router.get("/feature-flags",response_model=list[FlagView])
def flags(request:Request,p=Depends(admin)):
    with tenant_session(request.app.state.engine,p.school_id) as s:
        rows={x.key:x for x in s.scalars(select(FeatureFlag))}
        return [FlagView(key=k,enabled=rows[k].enabled if k in rows else True,revision=rows[k].revision if k in rows else 0) for k in ["missions","speech","notifications"]]

@router.put("/feature-flags/{key}",response_model=FlagView)
def set_flag(key:Literal["missions","speech","notifications"],body:FlagInput,request:Request,p=Depends(admin)):
    with tenant_session(request.app.state.engine,p.school_id) as s:
        s.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:k,0))"),{"k":f"flag:{p.school_id}:{key}"})
        row=s.scalar(select(FeatureFlag).where(FeatureFlag.key==key))
        if (row.revision if row else 0)!=body.expected_revision:raise HTTPException(409,"Révision modifiée.")
        if row:row.enabled=body.enabled;row.revision+=1;row.changed_by=p.user_id
        else:row=FeatureFlag(tenant_id=p.school_id,key=key,enabled=body.enabled,revision=1,changed_by=p.user_id);s.add(row)
        audit(s,p,"feature_flag.changed","feature_flag")
        return FlagView(key=key,enabled=row.enabled,revision=row.revision)

@router.get("/safety/events",response_model=list[EventView])
def events(request:Request,limit:int=Query(30,ge=1,le=100),offset:int=Query(0,ge=0,le=10000),p=Depends(admin)):
    with tenant_session(request.app.state.engine,p.school_id) as s:
        return [EventView(**{k:getattr(x,k) for k in EventView.model_fields}) for x in s.scalars(select(SafetyEvent).order_by(SafetyEvent.created_at.desc(),SafetyEvent.id).limit(limit).offset(offset))]

@router.post("/safety/events/{id}/review",response_model=CaseView)
def review_event(id:UUID,body:CaseInput,request:Request,p=Depends(admin)):
    with tenant_session(request.app.state.engine,p.school_id) as s:
        if not s.get(SafetyEvent,id):raise HTTPException(404,"Événement introuvable.")
        row=s.scalar(select(SafetyCase).where(SafetyCase.event_id==id))
        if row:
            if row.resolution!=body.resolution:raise HTTPException(409,"Événement déjà examiné.")
        else:
            row=SafetyCase(tenant_id=p.school_id,event_id=id,reviewer_id=p.user_id,resolution=body.resolution);s.add(row);s.flush()
            audit(s,p,"safety.reviewed","safety_event",id)
        return CaseView(id=row.id,resolution=row.resolution)

@router.get("/moderation/pending",response_model=list[Pending])
def pending(request:Request,p=Depends(require_roles("teacher","content_creator","school_admin","sys_admin"))):
    with tenant_session(request.app.state.engine,p.school_id) as s:
        result=[]
        for x in s.scalars(select(LessonVersion).where(LessonVersion.status=="pending_review").limit(100)):
            result.append(Pending(kind="lesson",id=x.id,content_id=x.lesson_id,version=x.version,review_path=f"/services/content-service/contents/{x.lesson_id}/versions/{x.version}/reviews"))
        for x in s.scalars(select(ExerciseVersion).where(ExerciseVersion.status=="in_review").limit(100)):
            result.append(Pending(kind="exercise",id=x.id,content_id=x.exercise_id,version=x.version,review_path=f"/services/exercise-service/exercises/{x.exercise_id}/versions/{x.version}/reviews"))
        for x in s.scalars(select(RagDocument).where(RagDocument.status=="pending_review").limit(100)):
            result.append(Pending(kind="rag",id=x.id,content_id=x.id,version=x.version,review_path=f"/services/retrieval-service/documents/{x.id}/review"))
        return result
