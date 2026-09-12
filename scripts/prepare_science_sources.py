"""Fetch the official PDF through the existing SSRF-safe ingestion reader.

Extract chapter pages as reviewable Markdown. Never marks them approved, never
invents embeddings. Production ingestion uses the generated ingestion requests.
"""
import argparse,hashlib,json
from pathlib import Path
from shared.service_loader import load_service
from shared.science.catalogue import PDF,COURSES

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    load_service("retrieval-service")
    from edu_retrieval_service.ingestion import fetch,extract,chunks
    data,mime=fetch(PDF)
    if mime!="application/pdf":raise ValueError("PDF officiel attendu")
    records=[]
    for entry in COURSES:
        pages=sorted(set([entry["science"]["source"]["page"]]+([7] if entry["chapter"]=="terre" else [])))
        body=extract(data,mime,pages,"science_2023_cm")
        (args.output/f"{entry['chapter']}.md").write_text(f"# {entry['title']}\n\nSource : {PDF}\n\nPages de l’annexe : {pages}\n\nStatut : colonne CM extraite, à relire avant approbation.\n\n{body}\n",encoding="utf-8")
        records.append({"chapter":entry["chapter"],"pages":pages,"characters":len(body),"chunks":len(chunks(body)),"status":"draft","sha256":hashlib.sha256(data).hexdigest()})
    (args.output/"manifest.json").write_text(json.dumps(records,indent=2),encoding="utf-8")
    print("4 extraits Markdown préparés ; colonnes et rattachement CM2 à relire. Aucun embedding créé.")

if __name__=="__main__":main()
