from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException,Request,Response
from sqlalchemy import select
from shared.ai.contracts import Strict
from shared.db.models import Student,ExerciseVersion
from shared.db.session import tenant_session
from shared.security.api import require_roles,enforce_rate
from shared.security.policy import consent_allowed
from shared.school import flag
from .engine import synthesize

router=APIRouter()
class Speak(Strict):
    exercise_version_id: UUID

@router.post("/synthesize",responses={200:{"description":"Consigne audio locale","content":{"audio/wav":{"schema":{"type":"string","format":"binary"}}}}},response_class=Response)
def speak(body:Speak,request:Request,p=Depends(require_roles("student"))):
    enforce_rate(request,"speak",p.user_id,10)
    with tenant_session(request.app.state.engine,p.school_id) as s:
        flag(s,"speech")
        student=s.scalar(select(Student).where(Student.user_id==p.user_id))
        if not student or not consent_allowed(s,student.id,"voice"):raise HTTPException(403,"Accord vocal requis.")
        prompt=s.scalar(select(ExerciseVersion.prompt).where(ExerciseVersion.id==body.exercise_version_id,ExerciseVersion.status=="published"))
        if not prompt:raise HTTPException(404,"Consigne publiée introuvable.")
        value=prompt.get("instruction","")
        if not value or len(value)>1500:raise HTTPException(422,"Consigne trop longue.")
    return Response(synthesize(value),media_type="audio/wav",headers={"Cache-Control":"no-store","Content-Disposition":"inline; filename=consigne.wav"})
