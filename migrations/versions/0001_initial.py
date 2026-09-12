"""Schéma initial figé : SQL indépendant des futurs modèles Python."""
from pathlib import Path
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None
SQL = Path(__file__).resolve().parents[1] / "sql"


def upgrade():
    op.execute((SQL / "0001_schema.sql").read_text(encoding="utf-8"))
    op.execute((SQL / "0001_security.sql").read_text(encoding="utf-8"))


def downgrade():
    op.execute((SQL / "0001_down.sql").read_text(encoding="utf-8"))
