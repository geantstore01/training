"""Privileged operator import of verified public material; never approves content.

The explicit owner can later submit drafts through the editorial API. Operational
audit entries have no human actor: this script does not impersonate a login or
manufacture reviews. Re-running skips matching source snapshots and exercise slugs.
"""
import argparse
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID
from sqlalchemy import create_engine, select, func
from shared.config import Settings
from shared.db.models import User, UserRole, ContentSource, RagDocument, RagPassage, Competency, Exercise
from shared.db.session import tenant_session
from shared.history.catalogue import COURSES
from shared.history.ingestion import history_chunks
from shared.exercises.cm2_pack import bind_exercises
from shared.ai.transport import embeddings
from shared.service_loader import load_service

def stage(engine,tenant,owner,root,settings,*,apply=False):
    manifest=json.loads((root/"manifest.json").read_text(encoding="utf-8"))
    if any("error" in row for row in manifest):raise ValueError("Toutes les sources doivent être vérifiées avant l’import")
    expected={(e["chapter"],s["url"],s["page"]) for e in COURSES for s in e["history"]["sources"]}
    if {(r["chapter"],r["url"],r["page"]) for r in manifest}!=expected:raise ValueError("Manifeste incompatible avec les sources du catalogue")
    groups={}
    for row in manifest:
        file=(root/row["file"]).resolve()
        if not file.is_relative_to(root.resolve()) or hashlib.sha256(file.read_bytes()).hexdigest()!=row["sha256"]:
            raise ValueError("Empreinte ou chemin de source invalide")
        extracted=(root/row["extracted"]).resolve()
        if not extracted.is_relative_to(root.resolve()):raise ValueError("Chemin d’extraction invalide")
        groups.setdefault((row["chapter"],row["url"]),[]).append(row)
    with tenant_session(engine,tenant) as session:
        if not session.scalar(select(User.id).join(UserRole,UserRole.user_id==User.id).where(User.id==owner,User.tenant_id==tenant,User.status=="active",UserRole.role=="content_creator")):
            raise ValueError("Propriétaire éditorial actif requis dans cette école")
        for entry in COURSES:
            comp=session.scalar(select(Competency).where(Competency.code==entry["code"],Competency.programme_version=="histoire-2020-cm2-2026"))
            if not comp or comp.objectives!=[entry["catalogue_objective"]]:raise ValueError("Migration et objectif historique exacts requis")
    if not apply:return dict(apply=False,documents=len(groups),exercises=sum(len(e["tasks"]) for e in COURSES),publication="none")
    counts=dict(sources_created=0,documents_created=0,passages_created=0,exercises_created=0,approved=0)
    source_ids={e["chapter"]:[] for e in COURSES}
    for (chapter,url),rows in groups.items():
        row=rows[0]
        text="\n\n".join((root/r["extracted"]).read_text(encoding="utf-8") for r in rows)
        parts=history_chunks(text)
        with tenant_session(engine,tenant) as session:
            source=session.scalar(select(ContentSource).where(ContentSource.tenant_id==tenant,ContentSource.checksum_sha256==row["sha256"]))
            if source is None:
                source=ContentSource(tenant_id=tenant,title=row["title"],url=url,publisher="Institution indiquée dans la référence",license="Conditions de réutilisation à vérifier avant redistribution",checksum_sha256=row["sha256"],retrieved_at=datetime.now(timezone.utc))
                session.add(source);session.flush();counts["sources_created"]+=1
            if source.url!=url:raise ValueError("Empreinte déjà associée à une autre URL : vérification opérateur requise")
            source_ids[chapter].append(source.id)
            old=session.scalar(select(RagDocument.id).where(RagDocument.tenant_id==tenant,RagDocument.url==url,RagDocument.history_chapter==chapter,RagDocument.checksum==row["sha256"]))
            if old:continue
            vectors=[]
            for offset in range(0,len(parts),16):vectors.extend(embeddings(settings,parts[offset:offset+16]))
            version=(session.scalar(select(func.max(RagDocument.version)).where(RagDocument.tenant_id==tenant,RagDocument.url==url,RagDocument.subject=="histoire",RagDocument.level=="CM2")) or 0)+1
            document=RagDocument(tenant_id=tenant,url=url,title=row["title"],checksum=row["sha256"],version=version,subject="histoire",level="CM2",history_chapter=chapter,programme_version="histoire-2020-cm2-2026",effective_from=date(2026,9,1),effective_until=date(2027,8,31),status="draft",created_by=owner,page_selection=sorted({r["page"] for r in rows if r["page"]}))
            session.add(document);session.flush()
            for i,(part,vector) in enumerate(zip(parts,vectors,strict=True)):
                session.add(RagPassage(tenant_id=tenant,document_id=document.id,ordinal=i,body=part,embedding=vector,embedding_model=settings.embedding_model))
            from shared.security.policy import audit
            audit(session,SimpleNamespace(school_id=tenant,user_id=None),"history.operator_import","rag_document",document.id)
            counts["documents_created"]+=1;counts["passages_created"]+=len(parts)
    load_service("exercise-service")
    from edu_exercise_service.routes import snapshot
    with tenant_session(engine,tenant) as session:
        for entry in COURSES:
            comp=session.scalar(select(Competency).where(Competency.code==entry["code"],Competency.programme_version=="histoire-2020-cm2-2026"))
            for i,candidate in enumerate(bind_exercises(entry,comp.id,source_ids[entry["chapter"]])):
                slug=entry["code"].lower()+f"-raisonner-v1-{i}"
                if session.scalar(select(Exercise.id).where(Exercise.tenant_id==tenant,Exercise.slug==slug)):continue
                item=Exercise(tenant_id=tenant,author_id=owner,slug=slug)
                session.add(item);session.flush()
                snapshot(session,item,candidate,1,SimpleNamespace(school_id=tenant,user_id=None))
                counts["exercises_created"]+=1
    return counts

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant",type=UUID,required=True)
    parser.add_argument("--owner",type=UUID,required=True)
    parser.add_argument("--sources",type=Path,required=True)
    parser.add_argument("--apply",action="store_true")
    args=parser.parse_args()
    settings=Settings(db_user="postgres",db_password_file=Path("/run/secrets/postgres_password"))
    engine=create_engine(settings.database_url())
    try:print(json.dumps(stage(engine,args.tenant,args.owner,args.sources,settings,apply=args.apply)))
    finally:engine.dispose()
