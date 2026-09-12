from pathlib import Path

from alembic import op


revision = "0008_cm2_catalogue"
down_revision = "0007_student_controls"
branch_labels = None
depends_on = None


def upgrade():
    op.execute((Path(__file__).resolve().parents[1] / "sql" / "0008_cm2_catalogue.sql").read_text(encoding="utf-8"))


def downgrade():
    op.execute("""DELETE FROM competency_prerequisites WHERE competency_id::text LIKE '00000000-0000-0000-0000-0000000008%' OR prerequisite_id::text LIKE '00000000-0000-0000-0000-0000000008%';
DELETE FROM competencies WHERE id::text LIKE '00000000-0000-0000-0000-0000000008%';
DELETE FROM curriculum_domains WHERE id::text LIKE '00000000-0000-0000-0000-0000000007%';
DELETE FROM subjects WHERE code='sciences';""")
