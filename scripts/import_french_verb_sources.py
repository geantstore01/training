"""Reproduce the checked intersection of two MIT-licensed conjugation datasets."""
import csv
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"shared/exercises/data"

def main():
    first=ROOT/"artifacts/reference-french-verbs"
    second=ROOT/"artifacts/reference-wordweaver"
    raw=json.loads((first/"verbs.json").read_text(encoding="utf-8"))["verbs"]
    rows=list(csv.DictReader((second/"Data/inputfile.csv").open(encoding="utf-8-sig")))
    index={(row["Verb"],row["option"],row["subject"]):row["text"] for row in rows}
    subjects=["1-sg","2-sg","3-sg-m","1-pl","2-pl","3-pl-m"]
    forms={};disagreements=[]
    for verb in raw:
        if verb["infinitive"] not in {"être","avoir","aller","faire"}:continue
        for tense in verb["tenses"]:
            if tense["name"] not in {"présent","imparfait","futur"}:continue
            name={"présent":"present","imparfait":"imparfait","futur":"futur"}[tense["name"]]
            for i,person in enumerate(tense["pronouns"]):
                key=f"{verb['infinitive']}|indicatif|{name}|{i}"
                expected=person["answer"]
                other=index.get((verb["infinitive"].replace("ê","e"),"indicatif-"+name,subjects[i]))
                if other!=expected:disagreements.append({"key":key,"first":expected,"second":other})
                else:forms[key]=expected
    OUTPUT.mkdir(parents=True,exist_ok=True)
    (OUTPUT/"french_verbs.json").write_text(json.dumps({"forms":forms,"excluded_disagreements":disagreements,"sources":[
        {"url":"https://github.com/andrewmcc/french-verbs","commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=first,text=True).strip()},
        {"url":"https://github.com/WordWeaverTools/WordWeaverLite","commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=second,text=True).strip()}]},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for folder,name in ((first,"french-verbs"),(second,"wordweaver")):
        shutil.copyfile(folder/"LICENSE",OUTPUT/f"LICENSE-{name}.txt")
    print(f"{len(forms)} formes concordantes importées ; {len(disagreements)} divergences exclues ; accents conservés.")

if __name__=="__main__":main()
