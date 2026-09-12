from pathlib import Path
from alembic import op
revision="0007_student_controls"
down_revision="0006_school_operations"
branch_labels=None
depends_on=None

def upgrade():
    op.execute((Path(__file__).resolve().parents[1]/"sql"/"0007_student_controls.sql").read_text(encoding="utf-8"))

def downgrade():
    op.execute("DROP TABLE tutor_controls")
