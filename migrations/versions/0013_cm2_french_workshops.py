from pathlib import Path
from alembic import op
revision="0013_cm2_french_workshops"
down_revision="0012_cm2_french_training"
branch_labels=None
depends_on=None
def upgrade():
    op.execute((Path(__file__).resolve().parents[1]/"sql/0013_cm2_french_workshops.sql").read_text(encoding="utf-8"))
def downgrade():
    pass
