from pathlib import Path
from alembic import op

revision = "0010_cm2_mathematics_catalogue"
down_revision = "0009_official_references_2026"
branch_labels = None
depends_on = None

def upgrade():
    op.execute((Path(__file__).resolve().parents[1] / "sql" / "0010_cm2_mathematics_catalogue.sql").read_text(encoding="utf-8"))

def downgrade():
    op.execute("DELETE FROM competencies WHERE code LIKE 'CM2-MATH-%' AND code NOT IN ('CM2-MATH-FRACTIONS','CM2-MATH-PROPORTION');")
