"""Vrai appel fournisseur, texte technique public uniquement. Aucun accès aux élèves."""
import json
from uuid import UUID
from shared.ai.transport import embeddings, post
from shared.ai.pedagogy import SYSTEM_PROMPT
from shared.ai.contracts import Plan
from shared.config import Settings

def main():
    settings = Settings()
    vector = embeddings(settings, ["Les fractions représentent des partages."], query=True)[0]
    source = "00000000-0000-0000-0000-000000000001"
    result = post(settings.ollama_url + "/api/chat", {"model":settings.cloud_model,"stream":False,"think":"low",
        "messages":[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":json.dumps({
            "niveau":0,"actions_autorisees":["reformuler"],"message":"Test technique sans données personnelles.",
            "sources":[{"id":source,"extrait":"Extrait synthétique destiné uniquement au test technique : comprendre la consigne."}]})}],
        "options":{"temperature":0,"num_predict":384}},timeout=25)
    plan = Plan.model_validate_json(result["message"]["content"])
    assert plan.action == "reformuler" and plan.source_id == UUID(source)
    print(json.dumps({"cloud_model":settings.cloud_model,"embedding_model":settings.embedding_model,"dimensions":len(vector),"structured_plan_valid":True}))

if __name__ == "__main__":
    main()
