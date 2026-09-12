"""Two-stage local editorial generation: model draft -> structural/scoped checks.

No generated text is automatically published or shown to a child. Semantic
grounding and scientific meaning require the existing independent human review.
"""
import json
import re
from copy import deepcopy
from shared.exercises.cm2_pack import bind_lesson, bind_exercises
from shared.service_loader import load_service
from .catalogue import BY_CHAPTER

def prepare(chapter,competency,source_ids,exercise_ids):
    entry=BY_CHAPTER[chapter]
    if not source_ids:raise ValueError("Source requise")
    candidates=bind_exercises(entry,competency["id"],source_ids)
    lesson=bind_lesson(entry,competency,source_ids,exercise_ids)
    return lesson,candidates

def validate_model_draft(raw,original):
    if len(raw)>60000:raise ValueError("Brouillon trop long")
    load_service("content-service")
    from edu_content_service.schemas import ContentInput
    candidate=ContentInput.model_validate_json(raw).model_dump(mode="json")
    expected=ContentInput.model_validate(original).model_dump(mode="json")
    # Model may rewrite only these two grounded paragraphs; all protocol, source,
    # exercise, objective, worked example and safety fields remain canonical.
    mutable=("discovery","explanation")
    for key in mutable:
        text=candidate["body"]["cm2"][key]
        if re.search(r"https?://|\b\d+\b|\b(flamm\w*|secteur|couteau|javel|ing[ée]r\w*|aval\w*|pression|four|micro-ondes)\b",text,re.I):
            raise ValueError("Instruction, mesure ou référence nouvelle à traiter hors génération automatique")
    checked=deepcopy(candidate)
    for key in mutable:checked["body"]["cm2"][key]=expected["body"]["cm2"][key]
    if checked!=expected:raise ValueError("Le modèle a changé un élément pédagogique protégé")
    return {"status":"draft","human_review_required":True,"validation":"structure_scope_and_protocol_only",
        "semantic_grounding":"requires_independent_human_review","lesson":candidate}

def generate_with_ollama(chapter,competency,source_ids,exercise_ids,passages,model,url="http://127.0.0.1:11434"):
    from urllib.parse import urlsplit
    import httpx
    from shared.ai.science_lesson_prompt import SCIENCE_LESSON_PROMPT
    parsed=urlsplit(url)
    if parsed.scheme!="http" or parsed.hostname not in {"127.0.0.1","localhost","ollama"} or parsed.username or parsed.password or parsed.path not in {"","/"}:
        raise ValueError("Endpoint Ollama local requis")
    if not 1<=len(passages)<=5 or any(p.get("status")!="approved" or p.get("level")!="CM2" or p.get("subject")!="sciences" for p in passages):
        raise ValueError("Extraits CM2 sciences approuvés requis")
    if any(str(p.get("source_id")) not in {str(i) for i in source_ids} or not p.get("body") for p in passages):
        raise ValueError("Les extraits ne correspondent pas aux sources fournies")
    original,_=prepare(chapter,competency,source_ids,exercise_ids)
    from .retrieval import retrieve
    passages=retrieve(original["body"]["cm2"]["objective"],passages,limit=3)
    if not passages:raise ValueError("Aucun extrait pertinent pour cette compétence")
    with httpx.Client(timeout=45,follow_redirects=False,trust_env=False) as client:
        with client.stream("POST",url.rstrip("/")+"/api/chat",json={"model":model,"stream":False,"format":"json","options":{"temperature":0,"num_predict":6000},"messages":[{"role":"system","content":SCIENCE_LESSON_PROMPT},{"role":"user","content":json.dumps({"lesson":original,"passages":[{"source_id":str(p["source_id"]),"body":p["body"][:4000]} for p in passages]},ensure_ascii=False)}]}) as response:
            response.raise_for_status();data=bytearray()
            for chunk in response.iter_bytes():
                data.extend(chunk)
                if len(data)>100000:raise ValueError("Réponse du modèle trop longue")
    return validate_model_draft(json.loads(data)["message"]["content"],original)
