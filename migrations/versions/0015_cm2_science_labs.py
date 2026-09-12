from pathlib import Path
from alembic import op
revision="0015_cm2_science_labs"
down_revision="0014_cm2_math_workshops"
branch_labels=None
depends_on=None

def upgrade():
    op.execute((Path(__file__).resolve().parents[1]/"sql/0015_cm2_science_labs.sql").read_text(encoding="utf-8"))

def downgrade():
    raise RuntimeError("Rollback requires an explicit notebook export and retention decision.")
