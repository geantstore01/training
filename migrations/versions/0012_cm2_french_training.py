from pathlib import Path
from alembic import op

revision="0012_cm2_french_training"
down_revision=("0011_cm2_fhs_catalogue","0011_cm2_lesson_links")
branch_labels=None
depends_on=None

def upgrade():
    op.execute((Path(__file__).resolve().parents[1]/"sql/0012_cm2_french_training.sql").read_text(encoding="utf-8"))

def downgrade():
    # Published curriculum may reference these immutable rows; preserve them.
    pass
