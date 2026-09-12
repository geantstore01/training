from alembic import op

revision = "0011_cm2_lesson_links"
down_revision = "0010_cm2_mathematics_catalogue"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("GRANT SELECT(id,tenant_id,status,difficulty) ON exercise_versions TO edu_content")
    op.execute("GRANT SELECT ON exercise_competencies TO edu_content")


def downgrade():
    op.execute("REVOKE SELECT(id,tenant_id,status,difficulty) ON exercise_versions FROM edu_content")
    op.execute("REVOKE SELECT ON exercise_competencies FROM edu_content")
