"""Editorial preparation under the current school's source and curriculum scope."""
from typing import Literal
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from shared.db.models import Competency, ContentSource, CurriculumLevel, Subject
from shared.db.session import tenant_session
from shared.security.api import require_roles, enforce_rate
from shared.security.tokens import Principal
from shared.history.catalogue import BY_CHAPTER
from shared.exercises.cm2_pack import bind_exercises, bind_lesson
from .schemas import ContentInput

router=APIRouter(prefix="/history",tags=["history-editorial"])

@router.get("/review-catalogue")
def review_catalogue(principal:Principal=Depends(require_roles("teacher","content_creator","school_admin","sys_admin"))):
    from shared.history.catalogue import COURSES
    return {"status":"draft","human_review_required":True,"courses":COURSES}

class DraftInput(BaseModel):
    model_config=ConfigDict(extra="forbid")
    chapter: Literal["ferry","republique","industrie","guerre-14","guerre-39","europe"]
    competency_id: UUID
    source_ids: list[UUID] = Field(min_length=1,max_length=10)
    published_exercise_ids: list[UUID] = Field(default_factory=list,max_length=3)

@router.post("/drafts/prepare")
def prepare(payload:DraftInput,request:Request,principal:Principal=Depends(require_roles("teacher","content_creator"))):
    enforce_rate(request,"history_prepare",principal.user_id,20)
    entry=BY_CHAPTER[payload.chapter]
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        comp=session.scalar(select(Competency).join(CurriculumLevel,CurriculumLevel.id==Competency.curriculum_level_id).join(Subject,Subject.id==Competency.subject_id).where(Competency.id==payload.competency_id,CurriculumLevel.code=="CM2",Subject.code=="histoire",Competency.programme_version=="histoire-2020-cm2-2026"))
        if not comp or comp.code!=entry["code"]:raise HTTPException(422,"Compétence historique incompatible.")
        sources=session.scalars(select(ContentSource).where(ContentSource.id.in_(payload.source_ids))).all()
        if len(sources)!=len(payload.source_ids):raise HTTPException(422,"Sources inconnues ou dupliquées.")
        required={s["url"] for s in entry["history"]["sources"]}
        if not required <= {s.url for s in sources}:raise HTTPException(422,"Toutes les sources du chapitre doivent être enregistrées dans l’école.")
        candidates=bind_exercises(entry,comp.id,payload.source_ids)
        lesson=None
        if payload.published_exercise_ids:
            if len(payload.published_exercise_ids)!=3:raise HTTPException(422,"Trois exercices requis.")
            lesson=ContentInput.model_validate(bind_lesson(entry,dict(id=str(comp.id),code=comp.code,objectives=comp.objectives),payload.source_ids,payload.published_exercise_ids)).model_dump(mode="json")
        return dict(status="draft",human_review_required=True,exercises=[c.model_dump(mode="json") for c in candidates],lesson=lesson,
            next_step="Créer et faire relire les exercices, puis créer la leçon liée. L’API de contenu vérifie les versions publiées avant tout enregistrement.")
