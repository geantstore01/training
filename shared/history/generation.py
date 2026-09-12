"""Deterministic source-bound draft creation; publication uses the existing review API."""
from copy import deepcopy
import json
from shared.exercises.cm2_pack import bind_exercises, bind_lesson
from shared.service_loader import load_service
from .catalogue import BY_CHAPTER
from .ingestion import extract_entities

def prepare(chapter,competency,source_ids,exercise_ids):
    entry=BY_CHAPTER[chapter]
    if not source_ids:raise ValueError("Source requise")
    lesson=bind_lesson(entry,competency,source_ids,exercise_ids)
    exercises=bind_exercises(entry,competency["id"],source_ids)
    load_service("content-service")
    from edu_content_service.schemas import ContentInput
    ContentInput.model_validate(lesson)
    return dict(status="draft",human_review_required=True,lesson=lesson,exercises=[e.model_dump(mode="json") for e in exercises])

def validate_model_draft(raw,original):
    if len(raw)>60_000:raise ValueError("Brouillon trop long")
    load_service("content-service")
    from edu_content_service.schemas import ContentInput
    value=ContentInput.model_validate_json(raw).model_dump(mode="json")
    expected=ContentInput.model_validate(original).model_dump(mode="json")
    check=deepcopy(value)
    chapter=expected["body"]["cm2"]["history"]["chapter"]
    for key in ("discovery","explanation"):
        original_dates={d["value"] for d in extract_entities(expected["body"]["cm2"][key],chapter)["dates"]}
        proposed_dates={d["value"] for d in extract_entities(check["body"]["cm2"][key],chapter)["dates"]}
        if proposed_dates-original_dates:raise ValueError("Date nouvelle dans la reformulation")
        check["body"]["cm2"][key]=expected["body"]["cm2"][key]
    if check!=expected:raise ValueError("Le modèle a changé une donnée historique protégée")
    return dict(status="draft",human_review_required=True,semantic_grounding="requires_human_review",lesson=value)

def generate_with_ollama(chapter,competency,source_ids,exercise_ids,passages,model,url="http://127.0.0.1:11434"):
    from urllib.parse import urlsplit
    import httpx
    from shared.ai.history_lesson_prompt import HISTORY_LESSON_PROMPT
    parsed=urlsplit(url)
    if parsed.scheme!="http" or parsed.hostname not in {"localhost","127.0.0.1","ollama"} or parsed.username or parsed.password or parsed.path not in {"","/"}:
        raise ValueError("Ollama local requis")
    if not 1<=len(passages)<=5 or any(p.get("status")!="approved" or p.get("subject")!="histoire" or p.get("level")!="CM2" or p.get("chapter")!=chapter or str(p.get("source_id")) not in {str(s) for s in source_ids} or not p.get("body") for p in passages):
        raise ValueError("Extraits approuvés du chapitre CM2 requis")
    original=prepare(chapter,competency,source_ids,exercise_ids)["lesson"]
    with httpx.Client(timeout=45,follow_redirects=False,trust_env=False) as client:
        with client.stream("POST",url.rstrip("/")+"/api/chat",json={"model":model,"stream":False,"format":"json","options":{"temperature":0,"num_predict":6000},"messages":[{"role":"system","content":HISTORY_LESSON_PROMPT},{"role":"user","content":json.dumps({"lesson":original,"passages":[{"source_id":str(p["source_id"]),"body":p["body"][:4000]} for p in passages]},ensure_ascii=False)}]}) as response:
            response.raise_for_status();data=bytearray()
            for chunk in response.iter_bytes():
                data.extend(chunk)
                if len(data)>100_000:raise ValueError("Réponse trop longue")
    return validate_model_draft(json.loads(data)["message"]["content"],original)
