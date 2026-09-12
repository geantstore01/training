from pathlib import Path
from alembic import op

revision = "0011_cm2_fhs_catalogue"
down_revision = "0010_cm2_mathematics_catalogue"
branch_labels = None
depends_on = None

def upgrade():
    op.execute((Path(__file__).resolve().parents[1] / "sql" / "0011_cm2_french_history_science_catalogue.sql").read_text(encoding="utf-8"))

def downgrade():
    op.execute("DELETE FROM competencies WHERE (code LIKE 'CM2-FR-%' OR code LIKE 'CM2-HIST-%' OR code LIKE 'CM2-SCI-%') AND programme_version='programme-cycle-3-reference-2020'")
