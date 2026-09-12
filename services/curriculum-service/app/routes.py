from datetime import date
from typing import Literal
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import or_, select, text
from shared.db.models import (Competency, CompetencyPrerequisite, CurriculumDomain, CurriculumLevel,
    MasteryRecord, Subject)
from shared.db.session import tenant_session
from shared.pedagogy import EvaluationLevel
from shared.security.api import current_principal, enforce_rate, require_roles
from shared.security.policy import accessible_student, audit
from shared.security.tokens import Principal
from .schemas import (CompetencyInput, CompetencyView, DomainInput, DomainView, EdgeInput, EdgeView,
    EvaluationView, GraphNode, GraphView, LevelView, SubjectView)

router = APIRouter(tags=["curriculum"])
# Shared national catalogue: a school's administrator/creator must not change it for all schools.
EDITOR = require_roles("sys_admin")

def present(session, cls, identifier):
    item = session.get(cls, identifier)
    if item is None:
        raise HTTPException(404, "Référence introuvable.")
    return item

@router.get("/subjects", response_model=list[SubjectView])
def subjects(request: Request, principal: Principal = Depends(current_principal)):
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        return [SubjectView.model_validate(x) for x in session.scalars(select(Subject).order_by(Subject.code))]

@router.get("/levels", response_model=list[LevelView])
def levels(request: Request, principal: Principal = Depends(current_principal)):
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        return [LevelView.model_validate(x) for x in session.scalars(select(CurriculumLevel).order_by(CurriculumLevel.code))]

@router.get("/evaluation-levels", response_model=list[EvaluationView])
def evaluation_levels(principal: Principal = Depends(current_principal)):
    return [EvaluationView(code=x, label=x.value.replace("_", " ")) for x in EvaluationLevel]

@router.get("/domains", response_model=list[DomainView])
def domains(request: Request, subject_id: UUID | None = None,
        limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0, le=10000),
        principal: Principal = Depends(current_principal)):
    query = select(CurriculumDomain)
    if subject_id: query = query.where(CurriculumDomain.subject_id == subject_id)
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        return [DomainView.model_validate(x) for x in session.scalars(query.order_by(CurriculumDomain.id).offset(offset).limit(limit))]

@router.post("/domains", response_model=DomainView, status_code=201)
def create_domain(payload: DomainInput, request: Request, principal: Principal = Depends(EDITOR)):
    enforce_rate(request, "edit", principal.user_id, 120)
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        subject = present(session, Subject, payload.subject_id)
        if subject.code not in {"francais", "mathematiques", "histoire", "sciences"}:
            raise HTTPException(422, "Matière hors périmètre.")
        item = CurriculumDomain(**payload.model_dump())
        session.add(item); session.flush()
        audit(session, principal, "curriculum.domain_created", "curriculum_domain", item.id)
        return DomainView.model_validate(item)

@router.post("/competencies", response_model=CompetencyView, status_code=201)
def create_competency(payload: CompetencyInput, request: Request, principal: Principal = Depends(EDITOR)):
    enforce_rate(request, "edit", principal.user_id, 120)
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        domain = present(session, CurriculumDomain, payload.domain_id)
        if domain.subject_id != payload.subject_id:
            raise HTTPException(422, "Domaine incompatible avec la matière.")
        present(session, CurriculumLevel, payload.curriculum_level_id)
        data = payload.model_dump(); data["official_reference_url"] = str(payload.official_reference_url)
        item = Competency(**data); session.add(item); session.flush()
        audit(session, principal, "curriculum.competency_created", "competency", item.id)
        return CompetencyView.model_validate(item)

@router.get("/competencies", response_model=list[CompetencyView])
def competencies(request: Request, subject_id: UUID | None = None, domain_id: UUID | None = None,
        level: Literal["CM1", "CM2"] | None = None, programme_version: str | None = Query(None, max_length=80),
        effective_on: date | None = None, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0, le=10000),
        principal: Principal = Depends(current_principal)):
    query = select(Competency).join(CurriculumLevel)
    for field,value in [(Competency.subject_id,subject_id),(Competency.domain_id,domain_id),(CurriculumLevel.code,level),(Competency.programme_version,programme_version)]:
        if value is not None: query = query.where(field == value)
    if effective_on:
        query = query.where(Competency.effective_from <= effective_on, or_(Competency.effective_until.is_(None), Competency.effective_until >= effective_on))
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        return [CompetencyView.model_validate(x) for x in session.scalars(query.order_by(Competency.code,Competency.id).offset(offset).limit(limit))]

@router.get("/competencies/{competency_id}", response_model=CompetencyView)
def competency(competency_id: UUID, request: Request, principal: Principal = Depends(current_principal)):
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        return CompetencyView.model_validate(present(session, Competency, competency_id))

@router.post("/competencies/{competency_id}/prerequisites", response_model=EdgeView, status_code=201)
def add_prerequisite(competency_id: UUID, payload: EdgeInput, request: Request, principal: Principal = Depends(EDITOR)):
    enforce_rate(request, "edit", principal.user_id, 120)
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        session.execute(text("SELECT pg_advisory_xact_lock(731241002)"))
        present(session, Competency, competency_id); present(session, Competency, payload.prerequisite_id)
        edge = CompetencyPrerequisite(competency_id=competency_id, prerequisite_id=payload.prerequisite_id)
        session.add(edge); session.flush()
        audit(session, principal, "curriculum.prerequisite_added", "competency", competency_id)
        return EdgeView.model_validate(edge)

@router.delete("/competencies/{competency_id}/prerequisites/{prerequisite_id}", status_code=204)
def remove_prerequisite(competency_id: UUID, prerequisite_id: UUID, request: Request, principal: Principal = Depends(EDITOR)):
    enforce_rate(request, "edit", principal.user_id, 120)
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        session.execute(text("SELECT pg_advisory_xact_lock(731241002)"))
        edge = session.scalar(select(CompetencyPrerequisite).where(CompetencyPrerequisite.competency_id==competency_id, CompetencyPrerequisite.prerequisite_id==prerequisite_id))
        if edge is None: raise HTTPException(404, "Prérequis introuvable.")
        session.delete(edge)
        audit(session, principal, "curriculum.prerequisite_removed", "competency", competency_id)

@router.get("/competencies/{competency_id}/graph", response_model=GraphView)
def graph(competency_id: UUID, request: Request, direction: Literal["upstream", "downstream"] = "upstream",
        max_depth: int = Query(10, ge=1, le=30), student_id: UUID | None = None,
        principal: Principal = Depends(current_principal)):
    enforce_rate(request, "graph", principal.user_id, 60)
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        present(session, Competency, competency_id)
        if student_id: accessible_student(session, principal, student_id)
        # Only fixed identifiers are interpolated; UUID/depth remain SQL parameters.
        source,target = ("competency_id","prerequisite_id") if direction=="upstream" else ("prerequisite_id","competency_id")
        session.execute(text("SET LOCAL statement_timeout='3000ms'"))
        rows = session.execute(text(f"""WITH RECURSIVE walk(id,depth) AS (
          SELECT CAST(:root AS uuid),0 UNION
          SELECT p.{target},w.depth+1 FROM competency_prerequisites p JOIN walk w ON p.{source}=w.id WHERE w.depth<:depth
        ) SELECT id,min(depth) AS distance FROM walk GROUP BY id ORDER BY min(depth),id LIMIT 201"""), {"root":competency_id,"depth":max_depth}).all()
        if len(rows)>200: raise HTTPException(422, "Graphe trop large : réduire la profondeur.")
        ids = [row.id for row in rows]
        items = {c.id:c for c in session.scalars(select(Competency).where(Competency.id.in_(ids)))}
        statuses = dict(session.execute(select(MasteryRecord.competency_id,MasteryRecord.evaluation_level).where(MasteryRecord.student_id==student_id,MasteryRecord.competency_id.in_(ids))).all()) if student_id else {}
        edges = list(session.scalars(select(CompetencyPrerequisite).where(CompetencyPrerequisite.competency_id.in_(ids),CompetencyPrerequisite.prerequisite_id.in_(ids)).order_by(CompetencyPrerequisite.competency_id,CompetencyPrerequisite.prerequisite_id)))
        boundary = [r.id for r in rows if r.distance==max_depth]
        cut = bool(boundary and session.scalar(select(CompetencyPrerequisite.id).where(getattr(CompetencyPrerequisite,source).in_(boundary),~getattr(CompetencyPrerequisite,target).in_(ids)).limit(1)))
        return GraphView(root_id=competency_id,direction=direction,max_depth=max_depth,truncated=cut,
            nodes=[GraphNode(competency=CompetencyView.model_validate(items[r.id]),distance=r.distance,
                evaluation_level=statuses.get(r.id,EvaluationLevel.NOT_EVALUATED) if student_id else None) for r in rows],
            edges=[EdgeView.model_validate(e) for e in edges])
