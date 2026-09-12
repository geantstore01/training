from pathlib import Path
from shared.history.catalogue import COURSES, PROGRAMME
from scripts.build_french_catalogue import build

def build_history():
    sql=build(COURSES).replace("French cycle 3","history cycle 3").replace(
        "00000000-0000-0000-0000-000000000702","00000000-0000-0000-0000-000000000703").replace(
        "00000000-0000-0000-0000-000000000201","00000000-0000-0000-0000-000000000203").replace(
        "https://www.education.gouv.fr/bo/2025/Hebdo16/MENE2504620A",PROGRAMME).replace("programme-2025-cm2-2026","histoire-2020-cm2-2026")
    sql+="ALTER TABLE rag_documents ADD COLUMN history_chapter VARCHAR(40);\n"
    sql+="ALTER TABLE rag_documents ADD CONSTRAINT ck_rag_documents_history_scope CHECK (history_chapter IS NULL OR (subject='histoire' AND level='CM2' AND history_chapter IN ('ferry','republique','industrie','guerre-14','guerre-39','europe')));\n"
    return sql+"\nUPDATE competencies SET effective_until='2027-08-31' WHERE programme_version='histoire-2020-cm2-2026';\n"

if __name__=="__main__":
    (Path(__file__).resolve().parents[1]/"migrations/sql/0016_cm2_history_workshops.sql").write_text(build_history(),encoding="utf-8")
