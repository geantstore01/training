from collections import Counter
from datetime import datetime,timezone
from decimal import Decimal
from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException,Query,Request
from sqlalchemy import func,select
from shared.db.models import (Competency,ContentReview,ContentSource,Exercise,ExerciseCompetency,
    ExerciseSource,ExerciseVersion,Hint,Subject)
from shared.db.session import tenant_session
from shared.security.api import current_principal,enforce_rate,require_roles
from shared.security.policy import audit
from shared.security.tokens import Principal
from shared.exercises.correctors import VERSION,grade
from shared.exercises.generation import generate
from shared.exercises.pipeline import validate
from shared.exercises.schemas import Candidate,PipelineReport,PublicPrompt,Responses,PartResult
from .schemas import CreateInput,GenerateInput,VersionInput,ExerciseView,EditorialView,ReviewInput

router=APIRouter(tags=["exercises"])
AUTHOR=require_roles("teacher","content_creator")
STAFF=require_roles("teacher","content_creator","school_admin","sys_admin")

def reference_sets(session,c):
    return (set(session.scalars(select(Competency.id).where(Competency.id.in_([p.competency_id for p in c.parts])))),
        set(session.scalars(select(ContentSource.id).where(ContentSource.id.in_(c.source_ids)))))

def candidate_from_version(session,v):
    if v.validator_name!="controlled" or v.validator_version!=VERSION:
        raise HTTPException(409,"Version non prise en charge par le correcteur contrôlé.")
    return Candidate(kind=v.kind,instruction=v.prompt["instruction"],parts=v.prompt["parts"],answers=v.answer_spec,
        source_ids=list(session.scalars(select(ExerciseSource.source_id).where(ExerciseSource.exercise_version_id==v.id))),
        difficulty=v.difficulty,hints=[dict(level=h.level,text=h.body["text"]) for h in session.scalars(select(Hint).where(Hint.exercise_version_id==v.id).order_by(Hint.level))])

def public(v):
    if v.validator_name!="controlled" or v.validator_version!=VERSION:
        raise HTTPException(409,"Version non prise en charge.")
    return ExerciseView(id=v.id,exercise_id=v.exercise_id,version=v.version,kind=v.kind,
        prompt=PublicPrompt.model_validate(v.prompt),difficulty=v.difficulty,status=v.status,published_at=v.published_at)

def editorial(session,v):
    return EditorialView(**public(v).model_dump(),candidate=candidate_from_version(session,v),
        pipeline=PipelineReport(passed=all(x["passed"] for x in v.pipeline_report),checks=v.pipeline_report))

def parent(session,identifier,lock=False):
    query=select(Exercise).where(Exercise.id==identifier)
    item=session.scalar(query.with_for_update() if lock else query)
    if item is None: raise HTTPException(404,"Exercice introuvable.")
    return item

def version(session,identifier,number):
    v=session.scalar(select(ExerciseVersion).where(ExerciseVersion.exercise_id==identifier,ExerciseVersion.version==number))
    if v is None: raise HTTPException(404,"Version introuvable.")
    return v

def owner(item,principal):
    if item.author_id!=principal.user_id: raise HTTPException(403,"Action réservée à l’auteur.")

def snapshot(session,item,c,number,principal):
    report=validate(c,*reference_sets(session,c))
    if not report.passed:
        raise HTTPException(422,"Validation refusée : "+", ".join(x.name for x in report.checks if not x.passed))
    v=ExerciseVersion(tenant_id=principal.school_id,exercise_id=item.id,version=number,kind=c.kind,
        prompt=PublicPrompt(instruction=c.instruction,parts=c.parts).model_dump(mode="json"),
        answer_spec={k:r.model_dump(mode="json") for k,r in c.answers.items()},validator_name="controlled",validator_version=VERSION,
        difficulty=c.difficulty,pipeline_report=[x.model_dump() for x in report.checks])
    session.add(v);session.flush()
    counts=Counter(p.competency_id for p in c.parts)
    session.add_all([ExerciseCompetency(tenant_id=principal.school_id,exercise_version_id=v.id,competency_id=k,
        weight=Decimal(n)/len(c.parts)) for k,n in counts.items()])
    session.add_all([ExerciseSource(tenant_id=principal.school_id,exercise_version_id=v.id,source_id=x) for x in c.source_ids])
    session.add_all([Hint(tenant_id=principal.school_id,exercise_version_id=v.id,level=h.level,body={"text":h.text}) for h in c.hints])
    session.flush();audit(session,principal,"exercise.version_created","exercise_version",v.id)
    return editorial(session,v)

@router.post("/validate",response_model=PipelineReport)
def validate_candidate(payload:Candidate,request:Request,principal:Principal=Depends(AUTHOR)):
    enforce_rate(request,"validate",principal.user_id,60)
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        return validate(payload,*reference_sets(session,payload))

@router.post("/exercises",response_model=EditorialView,status_code=201)
def create(payload:CreateInput,request:Request,principal:Principal=Depends(AUTHOR)):
    enforce_rate(request,"write",principal.user_id,30)
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        item=Exercise(tenant_id=principal.school_id,slug=payload.slug,author_id=principal.user_id)
        session.add(item);session.flush()
        return snapshot(session,item,payload.candidate,1,principal)

@router.post("/generate",response_model=EditorialView,status_code=201)
def generated(payload:GenerateInput,request:Request,principal:Principal=Depends(AUTHOR)):
    enforce_rate(request,"write",principal.user_id,30)
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        code=session.scalar(select(Subject.code).join(Competency,Competency.subject_id==Subject.id).where(Competency.id==payload.generation.competency_id))
        expected={"arithmetic":"mathematiques","agreement":"francais","chronology":"histoire"}[payload.generation.template]
        if code!=expected: raise HTTPException(422,"Compétence incompatible avec le modèle de génération.")
        item=Exercise(tenant_id=principal.school_id,slug=payload.slug,author_id=principal.user_id)
        session.add(item);session.flush()
        return snapshot(session,item,generate(payload.generation),1,principal)

@router.get("/exercises",response_model=list[ExerciseView])
def catalogue(request:Request,competency_id:UUID|None=None,limit:int=Query(30,ge=1,le=100),offset:int=Query(0,ge=0,le=10000),principal:Principal=Depends(current_principal)):
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        query=select(ExerciseVersion).where(ExerciseVersion.status=="published",ExerciseVersion.validator_name=="controlled",ExerciseVersion.validator_version==VERSION)
        if competency_id: query=query.where(ExerciseVersion.id.in_(select(ExerciseCompetency.exercise_version_id).where(ExerciseCompetency.competency_id==competency_id)))
        return [public(v) for v in session.scalars(query.order_by(ExerciseVersion.id).limit(limit).offset(offset))]

@router.get("/exercises/{exercise_id}/versions",response_model=list[EditorialView])
def history(exercise_id:UUID,request:Request,limit:int=Query(20,ge=1,le=100),offset:int=Query(0,ge=0,le=10000),principal:Principal=Depends(STAFF)):
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        parent(session,exercise_id)
        return [editorial(session,v) for v in session.scalars(select(ExerciseVersion).where(ExerciseVersion.exercise_id==exercise_id,ExerciseVersion.validator_name=="controlled").order_by(ExerciseVersion.version.desc()).limit(limit).offset(offset))]

@router.post("/exercises/{exercise_id}/versions",response_model=EditorialView,status_code=201)
def next_version(exercise_id:UUID,payload:VersionInput,request:Request,principal:Principal=Depends(AUTHOR)):
    enforce_rate(request,"write",principal.user_id,30)
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        item=parent(session,exercise_id,True);owner(item,principal)
        last=session.scalar(select(func.max(ExerciseVersion.version)).where(ExerciseVersion.exercise_id==exercise_id))
        if payload.base_version!=last: raise HTTPException(409,"Version de base obsolète.")
        return snapshot(session,item,payload.candidate,last+1,principal)

@router.get("/exercises/{exercise_id}/versions/{number}",response_model=ExerciseView)
def read(exercise_id:UUID,number:int,request:Request,principal:Principal=Depends(current_principal)):
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        v=version(session,exercise_id,number)
        if v.status!="published": raise HTTPException(404,"Version publiée introuvable.")
        return public(v)

@router.get("/exercises/{exercise_id}/versions/{number}/editorial",response_model=EditorialView)
def preview(exercise_id:UUID,number:int,request:Request,principal:Principal=Depends(STAFF)):
    with tenant_session(request.app.state.engine,principal.school_id) as session: return editorial(session,version(session,exercise_id,number))

@router.post("/exercises/{exercise_id}/versions/{number}/check-answer",response_model=list[PartResult])
def preview_grade(exercise_id:UUID,number:int,payload:Responses,request:Request,principal:Principal=Depends(AUTHOR)):
    enforce_rate(request,"validate",principal.user_id,60)
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        try: return grade(candidate_from_version(session,version(session,exercise_id,number)),payload.answers)
        except ValueError: raise HTTPException(422,"Réponses incompatibles.") from None

@router.post("/exercises/{exercise_id}/versions/{number}/submit",response_model=EditorialView)
def submit(exercise_id:UUID,number:int,request:Request,principal:Principal=Depends(AUTHOR)):
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        item=parent(session,exercise_id,True);owner(item,principal);v=version(session,exercise_id,number)
        last=session.scalar(select(func.max(ExerciseVersion.version)).where(ExerciseVersion.exercise_id==exercise_id))
        if v.status!="draft" or number!=last: raise HTTPException(409,"Dernier brouillon requis.")
        v.status="in_review";session.flush();session.refresh(v)
        audit(session,principal,"exercise.submitted","exercise_version",v.id)
        return editorial(session,v)

@router.post("/exercises/{exercise_id}/versions/{number}/reviews",response_model=EditorialView)
def review(exercise_id:UUID,number:int,payload:ReviewInput,request:Request,principal:Principal=Depends(AUTHOR)):
    enforce_rate(request,"write",principal.user_id,30)
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        item=parent(session,exercise_id,True);v=version(session,exercise_id,number)
        if item.author_id==principal.user_id: raise HTTPException(403,"Relecture indépendante requise.")
        last=session.scalar(select(func.max(ExerciseVersion.version)).where(ExerciseVersion.exercise_id==exercise_id))
        if v.status!="in_review" or number!=last: raise HTTPException(409,"Version en attente obsolète ou absente.")
        session.add(ContentReview(tenant_id=principal.school_id,exercise_version_id=v.id,reviewer_id=principal.user_id,decision=payload.decision,reason_code=payload.reason_code));session.flush()
        if payload.decision=="approved":
            for old in session.scalars(select(ExerciseVersion).where(ExerciseVersion.exercise_id==exercise_id,ExerciseVersion.status=="published")):
                old.status="retired"
            session.flush();v.status="published";v.published_at=datetime.now(timezone.utc)
        else: v.status="draft"
        session.flush();session.refresh(v);audit(session,principal,"exercise.review_"+payload.decision,"exercise_version",v.id)
        return editorial(session,v)

@router.post("/exercises/{exercise_id}/versions/{number}/archive",response_model=EditorialView)
def archive(exercise_id:UUID,number:int,request:Request,principal:Principal=Depends(STAFF)):
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        item=parent(session,exercise_id,True)
        if item.author_id!=principal.user_id and not principal.roles & {"school_admin","sys_admin"}: raise HTTPException(403,"Archivage interdit.")
        v=version(session,exercise_id,number)
        if v.status!="published": raise HTTPException(409,"Version publiée requise.")
        v.status="retired";session.flush();session.refresh(v);audit(session,principal,"exercise.archived","exercise_version",v.id)
        return editorial(session,v)


@router.get("/published/{version_id}",response_model=ExerciseView)
def published_version(version_id:UUID,request:Request,principal:Principal=Depends(current_principal)):
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        v=session.scalar(select(ExerciseVersion).where(ExerciseVersion.id==version_id,ExerciseVersion.status=="published",ExerciseVersion.validator_name=="controlled",ExerciseVersion.validator_version==VERSION))
        if v is None:raise HTTPException(404,"Exercice publié introuvable.")
        return public(v)

@router.get("/review-version/{version_id}",response_model=EditorialView)
def review_version(version_id:UUID,request:Request,principal:Principal=Depends(STAFF)):
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        v=session.get(ExerciseVersion,version_id)
        if v is None:raise HTTPException(404,"Version introuvable.")
        return editorial(session,v)
