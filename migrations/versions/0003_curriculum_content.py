"""Graphe pédagogique et validation humaine des versions de contenus."""
from pathlib import Path
from alembic import op
revision = "0003_curriculum_content"
down_revision = "0002_access_safety"
branch_labels = None
depends_on = None
SQL = Path(__file__).resolve().parents[1] / "sql"

def upgrade():
    op.execute((SQL / "0003_curriculum_content.sql").read_text(encoding="utf-8"))

def downgrade():
    op.execute((SQL / "0003_down.sql").read_text(encoding="utf-8"))
    original = (SQL / "0001_security.sql").read_text(encoding="utf-8")
    start = original.index("CREATE FUNCTION edu_guard_review()")
    stop = original.index("CREATE TRIGGER t10_review_guard", start)
    op.execute(original[start:stop].replace("CREATE FUNCTION", "CREATE OR REPLACE FUNCTION", 1)
        .replace("'teacher','moderator','tenant_admin'", "'teacher','school_admin','sys_admin'"))
    op.execute("CREATE TRIGGER t10_version_guard BEFORE INSERT OR UPDATE ON lesson_versions FOR EACH ROW EXECUTE FUNCTION edu_guard_version()")
