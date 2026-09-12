from shared.history.catalogue import COURSES as HISTORY_COURSES, public_catalogue as history_catalogue
"""Local acceptance fixture: real CM2 content and corrector, volatile anonymous state.

This does not replace the authenticated PostgreSQL services and is not deployed.
Run only on 127.0.0.1. No LLM or personal data is used.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from uuid import UUID, uuid4, uuid5, NAMESPACE_URL
from fastapi import FastAPI, HTTPException, Request
from shared.exercises.cm2_pack import COURSES, bind_exercises, bind_lesson
from shared.exercises.french_pack import COURSES as FRENCH_COURSES
from shared.science.catalogue import COURSES as SCIENCE_COURSES, public_catalogue
from shared.science.engine import ScienceInput, observe
from pydantic import ValidationError
from shared.exercises.french import dictation_feedback
from shared.exercises.schemas import PublicPrompt, Responses
from shared.exercises.correctors import grade
from shared.exercises.coaching import correction, diagnose
from shared.exercises.adaptive import choose_next
from shared.ai.pedagogy import render

app=FastAPI(title="Recette locale CM2 — données éphémères")
ROOT=Path(__file__).resolve().parents[1]
uid=lambda name:str(uuid5(NAMESPACE_URL,"educapilote-preview:"+name))
subject_id=uid("mathematics")
competencies=[];exercises={};lessons={};attempts={};sessions=set();science_runs={}
for filename in ("0008_cm2_catalogue.sql","0010_cm2_mathematics_catalogue.sql"):
    source=(ROOT/"migrations/sql"/filename).read_text(encoding="utf-8")
    for code,label,description,objectives in re.findall(r"'(CM2-MATH-[A-Z-]+)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'(\[[^']*\])'",source):
        competencies.append({"id":uid(code),"code":code,"label":label,"description":description,"objectives":json.loads(objectives),
            "common_errors":[],"subject_id":subject_id,"domain_id":uid("domain"),"curriculum_level_id":uid("CM2")})
for entry in COURSES[22:]:
    competencies.append({"id":uid(entry["code"]),"code":entry["code"],"label":entry["title"],
        "description":entry["catalogue_objective"],"objectives":[entry["catalogue_objective"]],
        "common_errors":entry["common_errors"],"subject_id":subject_id,"domain_id":uid("domain"),"curriculum_level_id":uid("CM2")})
for entry in FRENCH_COURSES:
    competencies.append({"id":uid(entry["code"]),"code":entry["code"],"label":entry["title"],
        "description":entry["catalogue_objective"],"objectives":[entry["catalogue_objective"]],
        "common_errors":entry["common_errors"],"subject_id":uid("french"),"domain_id":uid("french-domain"),"curriculum_level_id":uid("CM2")})
for entry in SCIENCE_COURSES:
    competencies.append({"id":uid(entry["code"]),"code":entry["code"],"label":entry["title"],
        "description":entry["catalogue_objective"],"objectives":[entry["catalogue_objective"]],
        "common_errors":entry["common_errors"],"subject_id":uid("sciences"),"domain_id":uid("science-domain"),"curriculum_level_id":uid("CM2")})
for entry in HISTORY_COURSES:
    competencies.append({"id":uid(entry["code"]),"code":entry["code"],"label":entry["title"],
        "description":entry["catalogue_objective"],"objectives":[entry["catalogue_objective"]],
        "common_errors":entry["common_errors"],"subject_id":uid("history"),"domain_id":uid("history-domain"),"curriculum_level_id":uid("CM2")})
for entry in COURSES+FRENCH_COURSES+SCIENCE_COURSES+HISTORY_COURSES:
    comp=next(c for c in competencies if c["code"]==entry["code"])
    identifiers=[]
    for index,candidate in enumerate(bind_exercises(entry,comp["id"],[uid("source")])):
        identifier=uid(entry["code"]+str(index));identifiers.append(identifier)
        exercises[identifier]=candidate
    lessons[comp["id"]]=bind_lesson(entry,comp,[uid("source")],identifiers)


def public(identifier):
    c=exercises[identifier]
    return {"id":identifier,"kind":c.kind,"difficulty":c.difficulty,"prompt":PublicPrompt(instruction=c.instruction,parts=c.parts).model_dump(mode="json")}


@app.get("/health")
def health():return {"mode":"local_acceptance_only","courses":len(lessons)}


@app.api_route("/api/{path:path}",methods=["GET","POST","DELETE"])
async def api(path:str,request:Request):
    body=await request.json() if request.method=="POST" else {}
    parts=path.split("/")
    if path=="assessment/history/catalogue":return history_catalogue()
    if path.endswith("/mastery"):return []
    if path=="assessment/science/catalogue":return public_catalogue()
    if path=="assessment/science/runs":
        raw={k:v for k,v in body.items() if k!="request_id"}
        try:
            payload=ScienceInput.model_validate(raw)
            request_id=str(UUID(body["request_id"]))
        except (ValidationError,ValueError,KeyError):raise HTTPException(422,"Choisis un réglage valide et écris ton hypothèse.")
        for row in science_runs.values():
            if row["request_id"]==request_id:
                if (row["chapter"],row["setting"],row["hypothesis"])!=(payload.chapter,payload.setting,payload.hypothesis):raise HTTPException(409,"Identifiant déjà utilisé.")
                return row
        identifier=str(uuid4())
        row={"id":identifier,"request_id":request_id,**payload.model_dump(),"result":observe(payload),"conclusion":"","completed_at":None,
            "created_at":datetime.now(timezone.utc).isoformat(),"review_status":"to_review","storage":"ephemeral_preview"}
        science_runs[identifier]=row;return row
    if path.startswith("assessment/science/runs/") and path.endswith("/conclusion"):
        row=science_runs.get(parts[3]);value=body.get("text","").strip()
        if not row:raise HTTPException(404,"Observation introuvable.")
        if not 3<=len(value)<=1000:raise HTTPException(422,"Écris une conclusion courte.")
        if row["completed_at"] and row["conclusion"]!=value:raise HTTPException(409,"Essai déjà terminé.")
        row.update(conclusion=value,completed_at=datetime.now(timezone.utc).isoformat());return row
    if path.startswith("assessment/science/notebook/"):
        if parts[3]!=uid("student"):raise HTTPException(404,"Carnet introuvable.")
        if request.method=="DELETE":
            science_runs.clear();return None
        return list(science_runs.values())[::-1]
    if path=="class/missions/today":return []
    if path.startswith("user/students/"):
        return {"id":uid("student"),"pseudonym":"Explorateur","level":"CM2","accessibility_preferences":{}}
    if path=="curriculum/subjects":return [{"id":subject_id,"code":"mathematiques","name":"Mathématiques"},{"id":uid("french"),"code":"francais","name":"Français"},{"id":uid("sciences"),"code":"sciences","name":"Sciences"},{"id":uid("history"),"code":"histoire","name":"Histoire"}]
    if path=="curriculum/competencies":return [c for c in competencies if not request.query_params.get("subject_id") or c["subject_id"]==request.query_params["subject_id"]]
    if path=="content/contents":
        key=request.query_params.get("competency_id")
        return [{"id":key,"version":1,"title":lessons[key]["title"]}] if key in lessons else []
    if path.startswith("content/contents/"):return lessons[parts[2]]
    if path=="exercise/exercises":
        comp=request.query_params.get("competency_id")
        return [public(key) for key,c in exercises.items() if str(c.parts[0].competency_id)==comp]
    if path.startswith("exercise/published/"):
        if parts[2] not in exercises:raise HTTPException(404,"Exercice absent")
        return public(parts[2])
    if path=="assessment/sessions":
        identifier=str(uuid4());sessions.add(identifier);return {"id":identifier}
    if path.startswith("assessment/sessions/") and path.endswith("/complete"):
        sessions.discard(parts[2]);return {"id":parts[2],"status":"completed"}
    if path=="assessment/attempts":
        if body["session_id"] not in sessions:raise HTTPException(409,"Session terminée")
        for row in attempts.values():
            if row["key"]==body["idempotency_key"]:return row["view"]
        identifier=str(uuid4())
        view={"id":identifier,"session_id":body["session_id"],"exercise_version_id":body["exercise_version_id"],"submitted_at":None,"result":None}
        attempts[identifier]={"key":body["idempotency_key"],"view":view,"level":0,"answers":{}}
        return view
    if path.startswith("assessment/attempts/"):
        row=attempts.get(parts[2])
        if not row:raise HTTPException(404,"Tentative absente")
        view=row["view"];candidate=exercises[view["exercise_version_id"]]
        if parts[3]=="submit":
            submitted=Responses.model_validate(body)
            if not any(str(value).strip() for value in submitted.answers.values()):raise HTTPException(422,"Écris une première réponse.")
            if view["submitted_at"]:
                if row["answers"]!=submitted.answers:raise HTTPException(409,"Essai déjà terminé")
                return view
            results=grade(candidate,submitted.answers);feedback=[]
            for result in results:
                diagnostic=diagnose(candidate.answers[result.part_id],submitted.answers.get(result.part_id)) if not result.correct else None
                review=result.error_code in {"HUMAN_REVIEW","FORMULATION_NOT_RECOGNIZED"}
                rule=candidate.answers[result.part_id]
                df=dictation_feedback(rule,submitted.answers.get(result.part_id,"")) if rule.mode=="dictation" and isinstance(submitted.answers.get(result.part_id,""),str) and not result.correct else None
                feedback.append({"part_id":result.part_id,"outcome":"réussi" if result.correct else "à_relire" if review else "à_revoir","error_code":result.error_code,
                    "categories":df["categories"] if df else [],
                    "message":"Tu as réussi cette étape. Explique ta méthode." if result.correct else df["message"] if df else "Ta réponse est à relire avec un enseignant. Elle n'est pas déclarée fausse." if review else diagnostic["message"] if diagnostic else "Observe les accents." if result.error_code=="ACCENT_ERROR" else "Repère le sujet et la forme du verbe." if result.error_code=="CONJUGATION_ERROR" else "Relis la consigne et ta réponse. Un indice peut t'aider."})
            row["answers"]=submitted.answers;row["reasoning"]=submitted.reasoning
            view.update(submitted_at=datetime.now(timezone.utc).isoformat(),result={"message":"Voici ce que ton essai nous apprend.","feedback":feedback})
            return view
        if parts[3]=="hints":
            level=int(parts[4])
            if level>row["level"]+1:raise HTTPException(409,"Lis l'indice précédent.")
            hint=next((h for h in candidate.hints if h.level==level),None)
            if not hint:raise HTTPException(404,"Indice absent")
            row["level"]=max(row["level"],level);return {"text":hint.text,"level":level}
        if parts[3]=="correction" and request.method=="POST":
            comp=next(c for c in competencies if c["id"]==str(candidate.parts[0].competency_id))
            if comp["subject_id"] not in {uid("french"),uid("sciences"),uid("history")} or body.get("explicit") is not True:raise HTTPException(409,"Demande explicite en français requise.")
            row["level"]=max(1,row["level"])
            return correction(candidate,set(candidate.answers))
        if not view["submitted_at"]:raise HTTPException(409,"Essaie avant de lire la correction.")
        if parts[3]=="correction":return correction(candidate,{key for key,value in row["answers"].items() if str(value).strip()})
        if parts[3]=="next":
            bank=[{"id":key,"difficulty":c.difficulty} for key,c in exercises.items() if c.parts[0].competency_id==candidate.parts[0].competency_id]
            review=all(f["outcome"]=="à_relire" for f in view["result"]["feedback"])
            return choose_next(bank,{r["view"]["exercise_version_id"] for r in list(attempts.values())[-20:]},candidate.difficulty,
                all(f["outcome"]=="réussi" for f in view["result"]["feedback"]) or review,row["level"]>0 or review)
    if path=="tutor/turns":
        row=attempts[body["attempt_id"]];candidate=exercises[row["view"]["exercise_version_id"]]
        row["level"]=min(2,row["level"]+1)
        reply=render(row["level"]);reply.message_pedagogique=candidate.hints[row["level"]-1].text
        return reply
    if path=="speech/synthesize":raise HTTPException(503,"L'audio n'est pas activé dans cette recette locale.")
    raise HTTPException(404,"Route de recette indisponible")
