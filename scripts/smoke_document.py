"""Vrai téléchargement officiel et extraction ; aucune publication ni donnée élève."""
import hashlib
import json
from shared.service_loader import load_service
from shared.ai.transport import embeddings
from shared.config import Settings

def main():
    from pathlib import Path
    if Path("services/retrieval-service").exists():
        load_service("retrieval-service")
        from edu_retrieval_service.ingestion import fetch, extract, chunks
    else:
        from app.ingestion import fetch, extract, chunks
    url="https://www.education.gouv.fr/sites/default/files/programme-de-math-matiques-pour-le-cycle-3-439827.pdf"
    data,mime=fetch(url)
    passages=chunks(extract(data,mime,[5,6]))
    vectors=embeddings(Settings(),passages[:2])
    print(json.dumps({"url":url,"sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data),"pages_tested":[5,6],
        "passages":len(passages),"vectors_tested":len(vectors),"dimensions":len(vectors[0]),"published":False}))

if __name__ == "__main__":
    main()
