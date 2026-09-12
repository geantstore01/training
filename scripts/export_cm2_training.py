"""Export reviewable API payloads bound to a real curriculum catalogue.

No remote mutation, no invented official references, no fake review signatures.
"""
import argparse
import json
from pathlib import Path
from uuid import UUID
from shared.exercises.cm2_pack import COURSES, bind_exercises, bind_lesson
from shared.service_loader import load_service


def export(catalogue, source_ids, published=None, subject="mathematiques"):
    if subject not in {"mathematiques","francais","sciences","histoire"}:raise ValueError("Matière non prise en charge")
    from shared.exercises.french_pack import COURSES as FRENCH_COURSES
    from shared.history.catalogue import COURSES as HISTORY_COURSES
    from shared.science.catalogue import COURSES as SCIENCE_COURSES
    by_code={row["code"]:row for row in catalogue}
    if len(by_code)!=len(catalogue):
        raise ValueError("Le contexte contient plusieurs versions du même code. Choisis la version active.")
    result={"format":"cm2-training-v1","publication":"requires_existing_editorial_review","courses":[],"missing_context":[]}
    for entry in HISTORY_COURSES if subject=="histoire" else SCIENCE_COURSES if subject=="sciences" else FRENCH_COURSES if subject=="francais" else COURSES:
        comp=by_code.get(entry["code"])
        if not comp:
            result["missing_context"].append(entry["code"]);continue
        candidates=bind_exercises(entry,comp["id"],source_ids)
        row={"code":entry["code"],"title":entry["title"],"exercises":[
            {"slug":entry["code"].lower()+f"-raisonner-v1-{i}","candidate":candidate.model_dump(mode="json")}
            for i,candidate in enumerate(candidates)]}
        if published and entry["code"] in published:
            load_service("content-service")
            from edu_content_service.schemas import ContentInput
            row["lesson"]=ContentInput.model_validate(bind_lesson(entry,comp,source_ids,published[entry["code"]])).model_dump(mode="json")
        else:
            row["lesson_pending"]="Fournir les trois identifiants de versions d'exercices publiées pour produire le contenu lié."
        result["courses"].append(row)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue",type=Path,required=True,help="Réponse JSON de curriculum/competencies?level=CM2&limit=100")
    parser.add_argument("--source-id",type=UUID,action="append",required=True,help="Source pédagogique déjà enregistrée dans l'école")
    parser.add_argument("--published",type=Path,help="Objet code → [version mini-question, exercice 1, exercice 2]")
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--subject",choices=["mathematiques","francais","sciences","histoire"],default="mathematiques")
    args=parser.parse_args()
    data=export(json.loads(args.catalogue.read_text(encoding="utf-8")),args.source_id,
        json.loads(args.published.read_text(encoding="utf-8")) if args.published else None,args.subject)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"{len(data['courses'])} cours préparés ; {len(data['missing_context'])} contextes manquants. Aucun contenu publié.")


if __name__=="__main__": main()
