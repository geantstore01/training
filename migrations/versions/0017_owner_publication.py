"""Explicit operator publication on the site owner's request, separate from human review."""
from alembic import op
revision='0017_owner_publication'
down_revision='0016_cm2_history_workshops'
branch_labels=None
depends_on=None

def upgrade():
    op.execute("""
    CREATE FUNCTION edu_owner_publication(t uuid, v uuid, kind text) RETURNS boolean
    LANGUAGE plpgsql AS $$ BEGIN
      IF session_user <> 'postgres' THEN RETURN false; END IF;
      RETURN EXISTS(SELECT 1 FROM audit_logs WHERE tenant_id=t AND resource_id=v
        AND resource_type=kind AND action='operator.owner_publication' AND outcome='success');
    END $$;
    DO $$ DECLARE definition text; BEGIN
      SELECT pg_get_functiondef('edu_guard_lesson_version()'::regprocedure) INTO definition;
      definition=replace(definition,'IF accepted IS DISTINCT FROM true THEN',
        'IF accepted IS DISTINCT FROM true AND NOT (NEW.status = ''approved'' AND edu_owner_publication(NEW.tenant_id,NEW.id,''lesson_version'')) THEN');
      EXECUTE definition;
      SELECT pg_get_functiondef('edu_guard_version()'::regprocedure) INTO definition;
      definition=replace(definition,'IF approved IS DISTINCT FROM true THEN',
        'IF approved IS DISTINCT FROM true AND NOT edu_owner_publication(NEW.tenant_id,NEW.id,''exercise_version'') THEN');
      EXECUTE definition;
    END $$;
    """)

def downgrade():
    op.execute("""DO $$ DECLARE definition text; BEGIN
      SELECT pg_get_functiondef('edu_guard_lesson_version()'::regprocedure) INTO definition;
      definition=replace(definition,'IF accepted IS DISTINCT FROM true AND NOT (NEW.status = ''approved'' AND edu_owner_publication(NEW.tenant_id,NEW.id,''lesson_version'')) THEN','IF accepted IS DISTINCT FROM true THEN'); EXECUTE definition;
      SELECT pg_get_functiondef('edu_guard_version()'::regprocedure) INTO definition;
      definition=replace(definition,'IF approved IS DISTINCT FROM true AND NOT edu_owner_publication(NEW.tenant_id,NEW.id,''exercise_version'') THEN','IF approved IS DISTINCT FROM true THEN'); EXECUTE definition;
    END $$; DROP FUNCTION edu_owner_publication(uuid,uuid,text);""")
