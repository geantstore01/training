from alembic import op

revision = "0009_official_references_2026"
down_revision = "0008_cm2_catalogue"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    UPDATE competencies SET official_reference_url='https://www.education.gouv.fr/bo/2025/Hebdo16/MENE2504620A', programme_version='programme-2025-cm2-2026'
      WHERE subject_id IN (SELECT id FROM subjects WHERE code IN ('francais','mathematiques'));
    UPDATE competencies SET official_reference_url='https://www.education.gouv.fr/bo/15/Special11/MENE1526483Aannexe2.htm', programme_version='programme-2020-cm2-2026'
      WHERE subject_id IN (SELECT id FROM subjects WHERE code IN ('histoire','sciences'));
    """)


def downgrade():
    op.execute("""
    UPDATE competencies SET official_reference_url='https://www.education.gouv.fr/bo/2025/Hebdo32/MENE2519535A', programme_version='programme-2025'
      WHERE code LIKE 'CM2-%';
    """)
