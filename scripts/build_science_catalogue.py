"""Reproducible four-chapter curriculum seed plus encrypted notebook migration."""
from pathlib import Path
from sqlalchemy.schema import CreateTable, CreateIndex
from sqlalchemy.dialects import postgresql
from shared.db.models import ScienceRun
from shared.science.catalogue import COURSES, SOURCE
from scripts.build_french_catalogue import build

def build_science():
    sql=build(COURSES).replace("French cycle 3", "science cycle 3").replace(
        "00000000-0000-0000-0000-000000000702","00000000-0000-0000-0000-000000000704").replace(
        "00000000-0000-0000-0000-000000000201","00000000-0000-0000-0000-000000000204").replace(
        "https://www.education.gouv.fr/bo/2025/Hebdo16/MENE2504620A",SOURCE).replace("programme-2025-cm2-2026","sciences-2023-cm2-2026")
    sql+="\nUPDATE competencies SET effective_until='2027-08-31' WHERE programme_version='sciences-2023-cm2-2026';\n"
    sql+="ALTER TABLE rag_documents DROP CONSTRAINT ck_rag_documents_subject_values;\nALTER TABLE rag_documents ADD CONSTRAINT ck_rag_documents_subject_values CHECK(subject IN ('francais','mathematiques','histoire','sciences'));\n"
    sql+=str(CreateTable(ScienceRun.__table__).compile(dialect=postgresql.dialect()))+";\n"
    for index in sorted(ScienceRun.__table__.indexes,key=lambda i:i.name):
        sql+=str(CreateIndex(index).compile(dialect=postgresql.dialect()))+";\n"
    sql+="""ALTER TABLE science_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE science_runs FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON science_runs USING(tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid) WITH CHECK(tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid);
CREATE TRIGGER t90_updated_at BEFORE UPDATE ON science_runs FOR EACH ROW EXECUTE FUNCTION edu_touch_updated_at();
GRANT SELECT,INSERT,UPDATE,DELETE ON science_runs TO edu_assessment;
GRANT SELECT,DELETE ON science_runs TO edu_notification;
"""
    return sql

if __name__=="__main__":
    (Path(__file__).resolve().parents[1]/"migrations/sql/0015_cm2_science_labs.sql").write_text(build_science(),encoding="utf-8")
