from datetime import datetime, timezone
import hashlib
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select, text
from shared.ai.contracts import Passage, SearchRequest, SearchResponse
from shared.ai.retrieval import HYBRID_SQL
from shared.ai.transport import embeddings, internal
from shared.db.models import RagDocument, RagPassage, RagReview
from shared.db.session import tenant_session
from shared.security.api import current_principal, enforce_rate, require_roles
from shared.security.policy import audit
from .ingestion import chunks, extract, fetch
from shared.history.ingestion import history_chunks, extract_entities
from .schemas import Document, Ingest, Review

router = APIRouter()
author = require_roles("teacher", "content_creator")

def dto(row):
    return Document.model_validate({key: getattr(row, key) for key in Document.model_fields})

def document(session, id, *, lock=False):
    query = select(RagDocument).where(RagDocument.id == id)
    row = session.scalar(query.with_for_update() if lock else query)
    if row is None:
        raise HTTPException(404, "Document introuvable.")
    return row

@router.post("/documents/ingest", response_model=Document, status_code=201)
def ingest(body: Ingest, request: Request, principal=Depends(author)):
    enforce_rate(request, "ingest", principal.school_id, 10, 3600)
    data, mime = fetch(body.url)
    from shared.science.catalogue import PDF
    scientific_cm=body.url==PDF and body.subject=="sciences" and body.level=="CM2"
    if scientific_cm and not body.page_selection:
        body=body.model_copy(update={"page_selection":[4,7,9,14]})
    try:
        extracted = extract(data,mime,body.page_selection,"science_2023_cm" if scientific_cm else "full")
        content = history_chunks(extracted) if body.subject=="histoire" else chunks(extracted)
    except ValueError:
        raise HTTPException(422, "Document inexploitable.") from None
    vectors = []
    for start in range(0, len(content), 32):
        vectors.extend(embeddings(request.app.state.settings, content[start:start+32]))
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key,0))"), {"key": f"rag:{principal.school_id}:{body.url}:{body.level}:{body.subject}"})
        version = session.scalar(select(func.max(RagDocument.version)).where(RagDocument.url == body.url, RagDocument.level == body.level, RagDocument.subject == body.subject)) or 0
        row = RagDocument(id=uuid4(), tenant_id=principal.school_id, **body.model_dump(), checksum=hashlib.sha256(data).hexdigest(), version=version+1, created_by=principal.user_id, status="draft")
        session.add(row)
        session.flush()
        for index, (chunk, vector) in enumerate(zip(content, vectors, strict=True)):
            session.add(RagPassage(tenant_id=principal.school_id, document_id=row.id, ordinal=index, body=chunk, embedding=vector, embedding_model=request.app.state.settings.embedding_model))
        audit(session, principal, "rag.ingested", "rag_document", row.id)
        return dto(row)

@router.get("/documents/{id}", response_model=Document)
def get_document(id: UUID, request: Request, principal=Depends(author)):
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        return dto(document(session, id))

@router.get("/documents/{id}/passages", response_model=list[Passage])
def get_passages(id: UUID, request: Request, principal=Depends(author)):
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        row = document(session, id)
        return [Passage(id=p.id, document_id=id, text=p.body, url=row.url, title=row.title, level=row.level, subject=row.subject, version=row.version)
            for p in session.scalars(select(RagPassage).where(RagPassage.document_id == id).order_by(RagPassage.ordinal))]

@router.post("/documents/{id}/submit", response_model=Document)
def submit(id: UUID, request: Request, principal=Depends(author)):
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        row = document(session, id, lock=True)
        if row.created_by != principal.user_id or row.status != "draft":
            raise HTTPException(409, "Brouillon personnel requis.")
        if not session.scalar(select(RagPassage.id).where(RagPassage.document_id == id).limit(1)):
            raise HTTPException(409, "Document sans passages.")
        row.status = "pending_review"
        audit(session, principal, "rag.submitted", "rag_document", id)
        session.flush()
        return dto(row)

@router.post("/documents/{id}/review", response_model=Document)
def review(id: UUID, body: Review, request: Request, principal=Depends(author)):
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        row = document(session, id, lock=True)
        if row.created_by == principal.user_id or row.status != "pending_review":
            raise HTTPException(409, "Relecteur indépendant et document en attente requis.")
        session.add(RagReview(tenant_id=principal.school_id, document_id=id, reviewer_id=principal.user_id, **body.model_dump(exclude={"confirmed_human_review"})))
        session.flush()
        row.status = "approved" if body.decision == "approved" else "draft"
        if row.status == "approved":
            row.approved_by, row.approved_at = principal.user_id, datetime.now(timezone.utc)
        audit(session, principal, "rag.reviewed", "rag_document", id)
        session.flush()
        return dto(row)

@router.post("/documents/{id}/archive", response_model=Document)
def archive(id: UUID, request: Request, principal=Depends(author)):
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        row = document(session, id, lock=True)
        if row.status != "approved":
            raise HTTPException(409, "Document approuvé requis.")
        row.status = "archived"
        audit(session, principal, "rag.archived", "rag_document", id)
        session.flush()
        return dto(row)

@router.post("/search", response_model=SearchResponse, dependencies=[Depends(internal)])
def search(body: SearchRequest, request: Request, principal=Depends(current_principal)):
    enforce_rate(request, "search", principal.user_id, 30)
    if body.subject=="histoire" and body.level=="CM2" and not body.history_chapter:
        raise HTTPException(422,"Choisis le chapitre historique avant la recherche.")
    query = body.query.get_secret_value()
    vector = embeddings(request.app.state.settings, [query], query=True)[0]
    with tenant_session(request.app.state.engine, principal.school_id) as session:
        statement=HYBRID_SQL
        params={}
        if body.history_chapter:
            if body.subject!="histoire" or body.level!="CM2":raise HTTPException(422,"Chapitre réservé à l’histoire CM2.")
            statement=text(str(HYBRID_SQL).replace("AND p.embedding_model=:model","AND p.embedding_model=:model AND d.history_chapter=:history_chapter"))
            params["history_chapter"]=body.history_chapter
        rows = session.execute(statement, {**params,"level": body.level, "subject": body.subject, "query": query,
            "vector": str(vector), "model": request.app.state.settings.embedding_model, "limit": body.limit}).mappings().all()
        return SearchResponse(passages=[Passage.model_validate(dict(row)) for row in rows], embedding_model=request.app.state.settings.embedding_model)


@router.get("/documents/{id}/history-entities")
def history_entities(id:UUID,request:Request,principal=Depends(author)):
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        row=document(session,id)
        if not row.history_chapter:raise HTTPException(409,"Document sans chapitre historique.")
        parts=session.scalars(select(RagPassage).where(RagPassage.document_id==id).order_by(RagPassage.ordinal)).all()
        return {"document_id":str(id),"url":row.url,"pages":row.page_selection,"passages":[{"id":str(p.id),**extract_entities(p.body,row.history_chapter)} for p in parts]}
