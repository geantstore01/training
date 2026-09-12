from pathlib import Path
from alembic import op
revision="0006_school_operations"
down_revision="0005_ai_rag_tutor"
branch_labels=None
depends_on=None
SQL=Path(__file__).resolve().parents[1]/"sql"
def upgrade():
    op.execute((SQL/"0006_school_operations.sql").read_text(encoding="utf-8"))
    op.execute((SQL/"0006_permissions.sql").read_text(encoding="utf-8"))
def downgrade():
    op.execute((SQL/"0006_down.sql").read_text(encoding="utf-8"))
