"""Authenticated, bounded scientific notebooks, independent from mastery scores."""
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, delete
from shared.db.models import ScienceRun, CurriculumLevel
from shared.db.session import tenant_session
from shared.security.api import current_principal, enforce_rate
from shared.security.policy import accessible_student, audit
from shared.security.tokens import Principal
from shared.science.engine import ScienceInput, observe
from shared.science.catalogue import public_catalogue
from .routes import own_student, LEARNER

router=APIRouter(prefix="/science",tags=["science"])

class RunInput(ScienceInput):
    request_id: UUID

class Conclusion(BaseModel):
    model_config=ConfigDict(extra="forbid",str_strip_whitespace=True)
    text: str=Field(min_length=3,max_length=1000)

def view(request,principal,row):
    notes=request.app.state.cipher.decrypt(row.notebook_ciphertext,school_id=principal.school_id,owner_id=row.id,purpose="science-notebook")
    return {"id":str(row.id),"chapter":row.chapter,"setting":row.setting,**notes,"result":row.observation,
        "completed_at":row.completed_at,"created_at":row.created_at,"review_status":"to_review","storage":"encrypted_30_days"}

@router.get("/catalogue")
def catalogue(principal:Principal=Depends(current_principal)):
    return public_catalogue()

@router.post("/runs")
def run(payload:RunInput,request:Request,principal:Principal=Depends(LEARNER)):
    enforce_rate(request,"science_run",principal.user_id,20)
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        student=own_student(session,principal,True)
        if session.scalar(select(CurriculumLevel.code).where(CurriculumLevel.id==student.curriculum_level_id))!="CM2":
            raise HTTPException(409,"Atelier réservé au niveau CM2.")
        now=datetime.now(timezone.utc)
        session.execute(delete(ScienceRun).where(ScienceRun.student_id==student.id,ScienceRun.expires_at<=now))
        old=session.scalar(select(ScienceRun).where(ScienceRun.student_id==student.id,ScienceRun.request_id==payload.request_id))
        if old:
            result=view(request,principal,old)
            if (old.chapter,old.setting,result["hypothesis"])!=(payload.chapter,payload.setting,payload.hypothesis):
                raise HTTPException(409,"Identifiant déjà utilisé pour un autre essai.")
            return result
        identifier=uuid4()
        row=ScienceRun(id=identifier,tenant_id=principal.school_id,student_id=student.id,request_id=payload.request_id,
            chapter=payload.chapter,setting=payload.setting,observation=observe(payload),expires_at=now+timedelta(days=30),
            notebook_ciphertext=request.app.state.cipher.encrypt({"hypothesis":payload.hypothesis,"conclusion":""},school_id=principal.school_id,owner_id=identifier,purpose="science-notebook"))
        session.add(row);session.flush();audit(session,principal,"science.observed","science_run",identifier)
        return view(request,principal,row)

@router.post("/runs/{run_id}/conclusion")
def conclude(run_id:UUID,payload:Conclusion,request:Request,principal:Principal=Depends(LEARNER)):
    enforce_rate(request,"science_conclude",principal.user_id,20)
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        student=own_student(session,principal,True)
        row=session.scalar(select(ScienceRun).where(ScienceRun.id==run_id,ScienceRun.student_id==student.id,ScienceRun.expires_at>datetime.now(timezone.utc)).with_for_update())
        if row is None:raise HTTPException(404,"Observation introuvable.")
        old=view(request,principal,row)
        if row.completed_at:
            if old["conclusion"]!=payload.text:raise HTTPException(409,"Cet essai est terminé. Lance une nouvelle comparaison.")
            return old
        row.notebook_ciphertext=request.app.state.cipher.encrypt({"hypothesis":old["hypothesis"],"conclusion":payload.text},school_id=principal.school_id,owner_id=row.id,purpose="science-notebook")
        row.completed_at=datetime.now(timezone.utc);session.flush()
        audit(session,principal,"science.concluded","science_run",row.id)
        return view(request,principal,row)

@router.get("/notebook/{student_id}")
def notebook(student_id:UUID,request:Request,principal:Principal=Depends(current_principal)):
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        accessible_student(session,principal,student_id)
        rows=session.scalars(select(ScienceRun).where(ScienceRun.student_id==student_id,ScienceRun.expires_at>datetime.now(timezone.utc)).order_by(ScienceRun.created_at.desc()).limit(100))
        return [view(request,principal,row) for row in rows]

@router.delete("/notebook/{student_id}",status_code=204)
def erase_notebook(student_id:UUID,request:Request,principal:Principal=Depends(LEARNER)):
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        student=own_student(session,principal,True)
        if student.id!=student_id:raise HTTPException(404,"Carnet introuvable.")
        session.execute(delete(ScienceRun).where(ScienceRun.student_id==student.id))
        audit(session,principal,"science.erased","student",student.id)
