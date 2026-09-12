"""Generate local staff-only ClassQuiz payloads and an explicit optional ZIM plan."""
import argparse,json
from pathlib import Path
from shared.science.integrations import classquiz_payload,offline_command,PHET
from shared.science.catalogue import BY_CHAPTER,PDF

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    for key in BY_CHAPTER:
        (args.output/f"classquiz-{key}.json").write_text(json.dumps(classquiz_payload(key),ensure_ascii=False,indent=2),encoding="utf-8")
    (args.output/"phet-delivery.json").write_text(json.dumps({"links":PHET,"optional_openzim_command":offline_command("./phet-output"),"executed":False,"offline_scope":"openZIM export requires a separate install and teacher review"},ensure_ascii=False,indent=2),encoding="utf-8")
    sources=[]
    for key,entry in BY_CHAPTER.items():
        sources.append({"url":PDF,"title":entry["title"]+" — extrait du programme 2023","level":"CM2","subject":"sciences",
            "programme_version":"sciences-2023-cm2-2026","effective_from":"2026-09-01","effective_until":"2027-08-31",
            "page_selection":sorted(set([entry["science"]["source"]["page"]]+([7] if key=="terre" else [])))})
    (args.output/"ingestion-requests.json").write_text(json.dumps(sources,ensure_ascii=False,indent=2),encoding="utf-8")
    print("4 fichiers ClassQuiz, 1 plan PhET/openZIM et 4 requêtes d’ingestion. Aucun envoi distant.")

if __name__=="__main__":main()
