"""Allow assessment to aggregate published lesson progress for an accessible student."""
from alembic import op

revision = "0018_course_progress_read"
down_revision = "0017_owner_publication"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("GRANT SELECT ON lessons, lesson_versions, lesson_competencies TO edu_assessment")


def downgrade():
    op.execute("REVOKE SELECT ON lessons, lesson_versions, lesson_competencies FROM edu_assessment")
