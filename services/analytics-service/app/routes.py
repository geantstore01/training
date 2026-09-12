from datetime import datetime,timedelta,timezone,date
from uuid import UUID
from fastapi import APIRouter,Depends,Request,Query
from sqlalchemy import select
from shared.db.session import tenant_session
from shared.security.api import current_principal,require_roles
from shared.security.policy import accessible_student,student_query
from shared.school import class_access
from shared.progression import ProgressSummary,summary
from shared.db.models import Enrollment

router=APIRouter()

@router.get("/students/{id}/dashboard",response_model=ProgressSummary)
def student(id:UUID,request:Request,days:int=Query(7,ge=1,le=90),p=Depends(current_principal)):
    with tenant_session(request.app.state.engine,p.school_id) as s:
        accessible_student(s,p,id);end=datetime.now(timezone.utc)
        return summary(s,id,end-timedelta(days=days),end)

@router.get("/dashboard",response_model=list[ProgressSummary])
def dashboard(request:Request,days:int=Query(7,ge=1,le=90),limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0,le=10000),p=Depends(require_roles("parent","teacher","school_admin","sys_admin"))):
    with tenant_session(request.app.state.engine,p.school_id) as s:
        end=datetime.now(timezone.utc)
        return [summary(s,x.id,end-timedelta(days=days),end) for x in s.scalars(student_query(p).limit(limit).offset(offset))]

@router.get("/classes/{id}/dashboard",response_model=list[ProgressSummary])
def class_dashboard(id:UUID,request:Request,days:int=Query(7,ge=1,le=90),p=Depends(require_roles("teacher","school_admin","sys_admin"))):
    from shared.db.models import Student
    with tenant_session(request.app.state.engine,p.school_id) as s:
        class_access(s,p,id);end=datetime.now(timezone.utc)
        ids=select(Enrollment.student_id).where(Enrollment.class_id==id,Enrollment.starts_on<=date.today(),(Enrollment.ends_on.is_(None))|(Enrollment.ends_on>=date.today()))
        return [summary(s,x.id,end-timedelta(days=days),end) for x in s.scalars(student_query(p).where(Student.id.in_(ids)).limit(100))]
