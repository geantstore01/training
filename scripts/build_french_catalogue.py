"""Regenerate the reviewable SQL seed from authored objectives, without database writes."""
import json
from pathlib import Path
from shared.exercises.french_pack import COURSES

ROOT=Path(__file__).resolve().parents[1]

def build(entries=None):
    def quote(value):return "'"+str(value).replace("'","''")+"'"
    rows=[]
    for entry in COURSES[:18] if entries is None else entries:
        # The pre-existing comprehension objective is retained exactly.
        values=["00000000-0000-0000-0000-000000000702","00000000-0000-0000-0000-000000000201",
            "00000000-0000-0000-0000-000000000102",entry["code"],entry["title"],entry["catalogue_objective"],
            json.dumps([entry["catalogue_objective"]],ensure_ascii=False),json.dumps(entry["common_errors"],ensure_ascii=False),
            "https://www.education.gouv.fr/bo/2025/Hebdo16/MENE2504620A","programme-2025-cm2-2026","2026-09-01"]
        rows.append(" ("+",".join(map(quote,values))+")")
    return "-- Original editorial objectives aligned with French cycle 3, CM2 September 2026.\n-- Internal codes, not official skill identifiers. Partial coverage; no publication of lessons.\nINSERT INTO competencies(domain_id,subject_id,curriculum_level_id,code,label,description,objectives,common_errors,official_reference_url,programme_version,effective_from) VALUES\n"+",\n".join(rows)+"\nON CONFLICT(code,programme_version) DO NOTHING;\n"

if __name__=="__main__":
    (ROOT/"migrations/sql/0012_cm2_french_training.sql").write_text(build(),encoding="utf-8")
    (ROOT/"migrations/sql/0013_cm2_french_workshops.sql").write_text(build(COURSES[18:]),encoding="utf-8")
