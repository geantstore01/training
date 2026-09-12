"""Produce SQL for the ten additional original math objectives, without DB writes."""
from pathlib import Path
from shared.exercises.cm2_pack import COURSES
from scripts.build_french_catalogue import build

def build_math():
    # Same SQL shape; replace only fixed subject/domain identifiers and header.
    sql=build(COURSES[22:]).replace("French cycle 3","mathematics cycle 3").replace(
        "00000000-0000-0000-0000-000000000702","00000000-0000-0000-0000-000000000701").replace(
        "00000000-0000-0000-0000-000000000201","00000000-0000-0000-0000-000000000202")
    lines=[]
    for line in sql.splitlines():
        if any(f"'CM2-MATH-{code}'" in line for code in ("CONTENANCES","RECTANGLES-COMPARER")):
            line=line.replace("00000000-0000-0000-0000-000000000701","00000000-0000-0000-0000-000000000705")
        elif "'CM2-MATH-DONNEES-COMPARER'" in line:
            line=line.replace("00000000-0000-0000-0000-000000000701","00000000-0000-0000-0000-000000000707")
        lines.append(line)
    return "\n".join(lines)+"\n"

if __name__=="__main__":
    (Path(__file__).resolve().parents[1]/"migrations/sql/0014_cm2_math_workshops.sql").write_text(build_math(),encoding="utf-8")
