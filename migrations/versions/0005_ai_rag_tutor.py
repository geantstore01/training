"""RAG officiel versionné et accompagnement socratique borné."""
from pathlib import Path
from alembic import op
revision = "0005_ai_rag_tutor"
down_revision = "0004_exercise_assessment"
branch_labels = None
depends_on = None
SQL = Path(__file__).resolve().parents[1] / "sql"

def upgrade():
    op.execute((SQL / "0005_ai_rag_tutor.sql").read_text(encoding="utf-8"))
    op.execute((SQL / "0005_ai_permissions.sql").read_text(encoding="utf-8"))

def downgrade():
    op.execute((SQL / "0005_down.sql").read_text(encoding="utf-8"))
