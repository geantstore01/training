from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from shared.db.models import (Competency, ContentReview, ContentSource, Lesson, LessonCompetency,
    LessonSource, LessonVersion)
from shared.db.session import tenant_session
from shared.security.api import current_principal, enforce_rate, require_roles
from shared.security.policy import audit
from shared.security.tokens import Principal
from .schemas import (ContentInput, ContentView, Kind, NextVersionInput, ReviewInput, ReviewView,
    SourceInput, SourceView, Status, VersionView, check_structure)

router = APIRouter(tags=["content"])
AUTHOR = require_roles("teacher", "content_creator")
STAFF_ROLES = {"teacher", "content_creator", "school_admin", "sys_admin"}
STAFF = require_roles(*STAFF_ROLES)

@router.get('/availability')
def availability(request:Request,principal:Principal=Depends(current_principal)):
    from shared.db.models import ExerciseCompetency,ExerciseVersion
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        exercises=select(ExerciseCompetency.competency_id).join(ExerciseVersion,ExerciseVersion.id==ExerciseCompetency.exercise_version_id).where(ExerciseVersion.status=='published')
        ids=session.scalars(select(LessonCompetency.competency_id).join(LessonVersion,LessonVersion.id==LessonCompetency.lesson_version_id).join(Lesson,Lesson.id==LessonVersion.lesson_id).where(LessonVersion.status=='approved',Lesson.kind=='lesson',LessonCompetency.competency_id.in_(exercises)).distinct()).all()
        return {'competency_ids':[str(x) for x in ids]}

def staff(principal):
    return bool(principal.roles & STAFF_ROLES)

def lesson_row(session,identifier,lock=False):
    query=select(Lesson).where(Lesson.id==identifier)
    item=session.scalar(query.with_for_update() if lock else query)
    if item is None: raise HTTPException(404,"Contenu introuvable.")
    return item

def version_row(session,lesson_id,number):
    item=session.scalar(select(LessonVersion).where(LessonVersion.lesson_id==lesson_id,LessonVersion.version==number))
    if item is None: raise HTTPException(404,"Version introuvable.")
    return item

def check_owner(lesson,principal):
    if lesson.author_id!=principal.user_id:
        raise HTTPException(403,"Seul l’auteur peut modifier ou soumettre ce contenu.")

def visible(lesson,version,principal):
    if not staff(principal) and (version.status!="approved" or lesson.kind=="teaching_sheet"):
        raise HTTPException(404,"Version introuvable.")

def view(session,lesson,version):
    return VersionView(id=version.id,lesson_id=lesson.id,version=version.version,title=version.title,
        body=version.body,status=version.status,kind=lesson.kind,editor_id=version.editor_id,
        review_round=version.review_round,published_at=version.published_at,created_at=version.created_at,
        competency_ids=list(session.scalars(select(LessonCompetency.competency_id).where(LessonCompetency.lesson_version_id==version.id).order_by(LessonCompetency.competency_id))),
        source_ids=list(session.scalars(select(LessonSource.source_id).where(LessonSource.lesson_version_id==version.id).order_by(LessonSource.source_id))))

def create_snapshot(session,lesson,payload,number,principal):
    try: check_structure(lesson.kind,payload.body)
    except ValueError as exc: raise HTTPException(422,str(exc)) from None
    found=set(session.scalars(select(Competency.id).where(Competency.id.in_(payload.competency_ids))))
    if found!=set(payload.competency_ids): raise HTTPException(422,"Compétence inconnue.")
    found=set(session.scalars(select(ContentSource.id).where(ContentSource.id.in_(payload.source_ids))))
    if found!=set(payload.source_ids): raise HTTPException(422,"Source inconnue dans cette école.")
    if payload.body.cm2:
        from shared.db.models import ExerciseVersion, ExerciseCompetency, CurriculumLevel, Subject
        course = payload.body.cm2
        if lesson.kind != "lesson" or course.objective not in payload.body.objectives:
            raise HTTPException(422,"Objectif de leçon incohérent.")
        scoped = session.execute(select(Competency, CurriculumLevel.code, Subject.code)
            .join(CurriculumLevel, CurriculumLevel.id==Competency.curriculum_level_id)
            .join(Subject, Subject.id==Competency.subject_id)
            .where(Competency.id.in_(payload.competency_ids))).all()
        if any(level != "CM2" or subject != course.subject for _,level,subject in scoped):
            raise HTTPException(422,"Le niveau ou la matière du parcours ne correspond pas aux compétences.")
        objectives = {objective for comp,_,_ in scoped for objective in comp.objectives}
        if not set(payload.body.objectives) <= objectives:
            raise HTTPException(422,"Utilise uniquement les objectifs du contexte pédagogique.")
        ids = [course.check_exercise_id, *course.practice_exercise_ids]
        for identifier in ids:
            exercise = session.execute(select(ExerciseVersion.id,ExerciseVersion.status,ExerciseVersion.difficulty).where(ExerciseVersion.id==identifier)).first()
            links = set(session.scalars(select(ExerciseCompetency.competency_id).where(ExerciseCompetency.exercise_version_id==identifier)))
            if exercise is None or exercise.status != "published" or not links or not links <= set(payload.competency_ids):
                raise HTTPException(422,"Exercice publié lié à la compétence requis.")
        difficulties = dict(session.execute(select(ExerciseVersion.id,ExerciseVersion.difficulty).where(ExerciseVersion.id.in_(ids))).all())
        if difficulties[ids[1]] > difficulties[ids[2]]:
            raise HTTPException(422,"Les exercices doivent être progressifs.")
    version=LessonVersion(tenant_id=principal.school_id,lesson_id=lesson.id,editor_id=principal.user_id,
        version=number,title=payload.title,body=payload.body.model_dump(mode="json"),status="draft")
    session.add(version); session.flush()
    session.add_all([LessonCompetency(tenant_id=principal.school_id,lesson_version_id=version.id,competency_id=x) for x in payload.competency_ids])
    session.add_all([LessonSource(tenant_id=principal.school_id,lesson_version_id=version.id,source_id=x) for x in payload.source_ids])
    session.flush()
    audit(session,principal,"content.version_created","lesson_version",version.id)
    return view(session,lesson,version)

@router.post("/sources",response_model=SourceView,status_code=201)
def source_create(payload:SourceInput,request:Request,principal:Principal=Depends(AUTHOR)):
    enforce_rate(request,"write",principal.user_id,60)
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        data=payload.model_dump(); data["url"]=str(payload.url)
        source=ContentSource(tenant_id=principal.school_id,**data); session.add(source); session.flush()
        audit(session,principal,"content.source_registered","content_source",source.id)
        return SourceView.model_validate(source)

@router.get("/sources",response_model=list[SourceView])
def sources(request:Request,limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0,le=10000),principal:Principal=Depends(STAFF)):
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        return [SourceView.model_validate(x) for x in session.scalars(select(ContentSource).order_by(ContentSource.id).limit(limit).offset(offset))]

@router.post("/contents",response_model=VersionView,status_code=201)
def create_content(payload:ContentInput,request:Request,principal:Principal=Depends(AUTHOR)):
    enforce_rate(request,"write",principal.user_id,60)
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        lesson=Lesson(tenant_id=principal.school_id,slug=payload.slug,kind=payload.kind,author_id=principal.user_id)
        session.add(lesson); session.flush()
        return create_snapshot(session,lesson,payload,1,principal)

@router.get("/contents",response_model=list[ContentView])
def contents(request:Request,kind:Kind|None=None,status:Status|None=None,competency_id:UUID|None=None,
        limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0,le=10000),principal:Principal=Depends(current_principal)):
    if not staff(principal) and status not in (None,"approved"):
        raise HTTPException(403,"Statut réservé à l’équipe pédagogique.")
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        versions=select(LessonVersion.lesson_id,func.max(LessonVersion.version).label("number"))
        if not staff(principal): versions=versions.where(LessonVersion.status=="approved")
        elif status: versions=versions.where(LessonVersion.status==status)
        versions=versions.group_by(LessonVersion.lesson_id).subquery()
        query=select(Lesson,LessonVersion).join(LessonVersion,LessonVersion.lesson_id==Lesson.id).join(versions,
            (versions.c.lesson_id==Lesson.id)&(versions.c.number==LessonVersion.version))
        if not staff(principal): query=query.where(Lesson.kind!="teaching_sheet")
        if kind: query=query.where(Lesson.kind==kind)
        if competency_id:
            query=query.where(LessonVersion.id.in_(select(LessonCompetency.lesson_version_id).where(LessonCompetency.competency_id==competency_id)))
        return [ContentView(id=l.id,slug=l.slug,kind=l.kind,author_id=l.author_id,version=v.version,version_id=v.id,title=v.title,status=v.status)
            for l,v in session.execute(query.order_by(Lesson.id).limit(limit).offset(offset))]

@router.get("/contents/{lesson_id}",response_model=VersionView)
def current_content(lesson_id:UUID,request:Request,principal:Principal=Depends(current_principal)):
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        lesson=lesson_row(session,lesson_id)
        query=select(LessonVersion).where(LessonVersion.lesson_id==lesson_id,LessonVersion.status=="approved")
        version=session.scalar(query)
        if version is None: raise HTTPException(404,"Aucune version approuvée.")
        visible(lesson,version,principal)
        return view(session,lesson,version)

@router.get("/contents/{lesson_id}/versions",response_model=list[VersionView])
def history(lesson_id:UUID,request:Request,limit:int=Query(20,ge=1,le=100),offset:int=Query(0,ge=0,le=10000),principal:Principal=Depends(STAFF)):
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        lesson=lesson_row(session,lesson_id)
        return [view(session,lesson,v) for v in session.scalars(select(LessonVersion).where(LessonVersion.lesson_id==lesson_id).order_by(LessonVersion.version.desc()).limit(limit).offset(offset))]

@router.get("/contents/{lesson_id}/versions/{number}",response_model=VersionView)
def get_version(lesson_id:UUID,number:int,request:Request,principal:Principal=Depends(current_principal)):
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        lesson=lesson_row(session,lesson_id); version=version_row(session,lesson_id,number)
        visible(lesson,version,principal)
        return view(session,lesson,version)

@router.post("/contents/{lesson_id}/versions",response_model=VersionView,status_code=201)
def new_version(lesson_id:UUID,payload:NextVersionInput,request:Request,principal:Principal=Depends(AUTHOR)):
    enforce_rate(request,"write",principal.user_id,60)
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        lesson=lesson_row(session,lesson_id,lock=True); check_owner(lesson,principal)
        last=session.scalar(select(func.max(LessonVersion.version)).where(LessonVersion.lesson_id==lesson_id))
        if payload.base_version!=last: raise HTTPException(409,"Version de base obsolète.")
        return create_snapshot(session,lesson,payload,last+1,principal)

@router.post("/contents/{lesson_id}/versions/{number}/submit",response_model=VersionView)
def submit(lesson_id:UUID,number:int,request:Request,principal:Principal=Depends(AUTHOR)):
    enforce_rate(request,"write",principal.user_id,60)
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        lesson=lesson_row(session,lesson_id,lock=True); check_owner(lesson,principal)
        version=version_row(session,lesson_id,number)
        last=session.scalar(select(func.max(LessonVersion.version)).where(LessonVersion.lesson_id==lesson_id))
        if version.status!="draft" or number!=last: raise HTTPException(409,"Seule la dernière version brouillon peut être soumise.")
        version.status="pending_review"; session.flush(); session.refresh(version)
        audit(session,principal,"content.submitted","lesson_version",version.id)
        return view(session,lesson,version)

@router.post("/contents/{lesson_id}/versions/{number}/reviews",response_model=ReviewView,status_code=201)
def review(lesson_id:UUID,number:int,payload:ReviewInput,request:Request,principal:Principal=Depends(AUTHOR)):
    enforce_rate(request,"write",principal.user_id,60)
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        lesson=lesson_row(session,lesson_id,lock=True); version=version_row(session,lesson_id,number)
        if principal.user_id in (lesson.author_id,version.editor_id): raise HTTPException(403,"Une relecture indépendante est obligatoire.")
        if version.status!="pending_review": raise HTTPException(409,"Version non soumise à relecture.")
        last=session.scalar(select(func.max(LessonVersion.version)).where(LessonVersion.lesson_id==lesson_id))
        if number!=last: raise HTTPException(409,"Une version plus récente existe.")
        if payload.decision=="approved" and version.body.get("cm2"):
            from shared.db.models import ExerciseVersion,ExerciseCompetency
            course=version.body['cm2']
            ids=[UUID(course['check_exercise_id']),*[UUID(x) for x in course['practice_exercise_ids']]]
            allowed=set(session.scalars(select(LessonCompetency.competency_id).where(LessonCompetency.lesson_version_id==version.id)))
            for identifier in ids:
                exercise=session.execute(select(ExerciseVersion.id,ExerciseVersion.status).where(ExerciseVersion.id==identifier)).first()
                links=set(session.scalars(select(ExerciseCompetency.competency_id).where(ExerciseCompetency.exercise_version_id==identifier)))
                if exercise is None or exercise.status!='published' or not links or not links<=allowed:
                    raise HTTPException(422,'Valide les trois exercices liés avant de publier la leçon.')
        record=ContentReview(tenant_id=principal.school_id,lesson_version_id=version.id,reviewer_id=principal.user_id,
            decision=payload.decision,reason_code=payload.reason_code)
        session.add(record); session.flush(); session.refresh(record)
        if payload.decision=="approved":
            previous=session.scalar(select(LessonVersion).where(LessonVersion.lesson_id==lesson_id,LessonVersion.status=="approved"))
            if previous: previous.status="archived"; session.flush()
            version.status="approved"
        else: version.status="draft"
        session.flush()
        audit(session,principal,"content.review_"+payload.decision,"lesson_version",version.id)
        return ReviewView.model_validate(record)

@router.get("/contents/{lesson_id}/versions/{number}/reviews",response_model=list[ReviewView])
def reviews(lesson_id:UUID,number:int,request:Request,limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0,le=10000),principal:Principal=Depends(STAFF)):
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        lesson_row(session,lesson_id); version=version_row(session,lesson_id,number)
        return [ReviewView.model_validate(r) for r in session.scalars(select(ContentReview).where(ContentReview.lesson_version_id==version.id).order_by(ContentReview.reviewed_at,ContentReview.id).limit(limit).offset(offset))]

@router.post("/contents/{lesson_id}/versions/{number}/archive",response_model=VersionView)
def archive(lesson_id:UUID,number:int,request:Request,principal:Principal=Depends(STAFF)):
    enforce_rate(request,"write",principal.user_id,60)
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        lesson=lesson_row(session,lesson_id,lock=True)
        if lesson.author_id!=principal.user_id and not principal.roles & {"school_admin","sys_admin"}:
            raise HTTPException(403,"Archivage non autorisé.")
        version=version_row(session,lesson_id,number)
        if version.status=="archived": raise HTTPException(409,"Version déjà archivée.")
        version.status="archived"; session.flush(); session.refresh(version)
        audit(session,principal,"content.archived","lesson_version",version.id)
        return view(session,lesson,version)
