from pathlib import Path
from alembic import op
revision="0016_cm2_history_workshops"
down_revision="0015_cm2_science_labs"
branch_labels=None
depends_on=None

def upgrade():
    op.execute((Path(__file__).resolve().parents[1]/"sql/0016_cm2_history_workshops.sql").read_text(encoding="utf-8"))

def downgrade():
    # Preserve curriculum rows referenced by published material and attempts.
    pass
