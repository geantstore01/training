"""Prepare a complete review dossier and interoperability exports, without publishing."""
import argparse
import json
from pathlib import Path
from shared.history.catalogue import COURSES, PROGRAMME
from shared.history.integrations import classquiz_payload, interactive_quiz_payload, quizli_csv

def export(root):
    root.mkdir(parents=True,exist_ok=True)
    for entry in COURSES:
        key=entry["chapter"]
        for name,data in [("review",dict(status="draft",human_review_required=True,course=entry)),("classquiz",classquiz_payload(key)),("interactive-quiz-maker",interactive_quiz_payload(key))]:
            (root/f"{key}-{name}.json").write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
        (root/f"{key}-quizli.csv").write_text(quizli_csv(key),encoding="utf-8")
    requests=[]
    for entry in COURSES:
        for s in entry["history"]["sources"]:
            requests.append(dict(url=s["url"],title=s["title"],subject="histoire",level="CM2",history_chapter=entry["chapter"],programme_version="histoire-2020-cm2-2026",effective_from="2026-09-01",effective_until="2027-08-31",page_selection=[s["page"]] if s["page"] else []))
    (root/"ingestion-requests.json").write_text(json.dumps(requests,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"{len(COURSES)} dossiers complets préparés. Aucune publication. Programme : {PROGRAMME}")

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=Path("artifacts/history-review"))
    export(parser.parse_args().output)
