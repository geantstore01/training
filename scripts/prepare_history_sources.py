"""Download the cited institutional sources and retain hashes/extraction for adult review."""
import hashlib
import json
from pathlib import Path
from shared.history.catalogue import COURSES
from shared.history.ingestion import extract_entities
from shared.service_loader import load_service

def main():
    load_service("retrieval-service")
    from edu_retrieval_service.ingestion import fetch, extract
    root=Path("artifacts/history-sources");root.mkdir(parents=True,exist_ok=True)
    cache={};manifest=[]
    for entry in COURSES:
        for source in entry["history"]["sources"]:
            row={**source,"chapter":entry["chapter"],"status":"draft","human_review_required":True}
            try:
                if source["url"] not in cache:cache[source["url"]]=fetch(source["url"])
                data,mime=cache[source["url"]]
                digest=hashlib.sha256(data).hexdigest()
                name=digest+(".pdf" if mime=="application/pdf" else ".html" if "html" in mime else ".txt")
                (root/name).write_bytes(data)
                text=extract(data,mime,[source["page"]] if source["page"] else [])
                extracted=f'{entry["chapter"]}-{digest[:12]}-p{source["page"] or 0}.txt'
                (root/extracted).write_text(text,encoding="utf-8")
                row.update(sha256=digest,file=name,extracted=extracted,entities=extract_entities(text,entry["chapter"]))
                print(entry["chapter"],source["title"],"OK",flush=True)
            except Exception as exc:
                row["error"]=type(exc).__name__
                print(entry["chapter"],source["title"],row["error"],flush=True)
            manifest.append(row)
    (root/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")

if __name__=="__main__":main()
