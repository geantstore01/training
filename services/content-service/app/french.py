"""Teacher-only review queue for the installed French workshops."""
from fastapi import APIRouter,Depends,Request
from sqlalchemy import select
from shared.db.models import Lesson,LessonVersion
from shared.db.session import tenant_session
from shared.security.api import require_roles
from shared.security.tokens import Principal
router=APIRouter(prefix='/french',tags=['french-editorial'])

@router.get('/review-catalogue')
def catalogue(request:Request,principal:Principal=Depends(require_roles('teacher','content_creator','school_admin','sys_admin'))):
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        rows=session.execute(select(Lesson,LessonVersion).join(LessonVersion,LessonVersion.lesson_id==Lesson.id).where(Lesson.slug.like('cm2-fr-%-atelier-francais'),LessonVersion.version==1).order_by(LessonVersion.title)).all()
        return {'courses':[dict(id=str(l.id),version=v.version,title=v.title,body=v.body,status=v.status,author_id=str(l.author_id)) for l,v in rows]}
