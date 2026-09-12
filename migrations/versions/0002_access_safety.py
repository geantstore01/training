"""Accès par école, six rôles, identités chiffrées et consentements append-only."""
from pathlib import Path
from alembic import op

revision = "0002_access_safety"
down_revision = "0001_initial"
branch_labels = None
depends_on = None
SQL = Path(__file__).resolve().parents[1] / "sql"


def upgrade():
    op.execute((SQL / "0002_access_safety.sql").read_text(encoding="utf-8"))


def downgrade():
    op.execute((SQL / "0002_down.sql").read_text(encoding="utf-8"))
    original = (SQL / "0001_security.sql").read_text(encoding="utf-8")
    for function, trigger in [("edu_check_consent", "t10_consent_guard"), ("edu_guard_review", "t10_review_guard")]:
        start = original.index(f"CREATE FUNCTION {function}()")
        stop = original.index(f"CREATE TRIGGER {trigger}", start)
        op.execute(original[start:stop].replace("CREATE FUNCTION", "CREATE OR REPLACE FUNCTION", 1))
    op.execute("CREATE TRIGGER t10_consent_guard BEFORE INSERT OR UPDATE ON consent_records FOR EACH ROW EXECUTE FUNCTION edu_check_consent()")
