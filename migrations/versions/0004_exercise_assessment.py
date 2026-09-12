"""Exercices contrôlés et preuves de maîtrise transactionnelles."""
from pathlib import Path
from alembic import op
revision="0004_exercise_assessment"
down_revision="0003_curriculum_content"
branch_labels=None
depends_on=None
SQL=Path(__file__).resolve().parents[1]/"sql"

def review_function():
    original=(SQL/"0003_curriculum_content.sql").read_text(encoding="utf-8")
    start=original.index("CREATE OR REPLACE FUNCTION edu_guard_review()")
    stop=original.index("CREATE FUNCTION edu_immutable_content_record()",start)
    return original[start:stop]

def upgrade():
    op.execute((SQL/"0004_exercise_assessment.sql").read_text(encoding="utf-8"))
    op.execute(review_function().replace("r.role IN ('teacher','school_admin','sys_admin')", "r.role IN ('teacher','content_creator')"))

def downgrade():
    op.execute((SQL/"0004_down.sql").read_text(encoding="utf-8"))
    op.execute(review_function())
