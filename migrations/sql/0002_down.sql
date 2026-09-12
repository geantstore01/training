-- Refuser une perte de preuves/PII. Le rollback reste possible sur une base vide de données du module 2.
ALTER TABLE schools DISABLE ROW LEVEL SECURITY;
ALTER TABLE students DISABLE ROW LEVEL SECURITY;
ALTER TABLE guardian_students DISABLE ROW LEVEL SECURITY;
ALTER TABLE consent_records DISABLE ROW LEVEL SECURITY;
ALTER TABLE student_assents DISABLE ROW LEVEL SECURITY;
ALTER TABLE safety_events DISABLE ROW LEVEL SECURITY;
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM consent_records WHERE event_type <> 'legacy')
    OR EXISTS (SELECT 1 FROM student_assents)
    OR EXISTS (SELECT 1 FROM students WHERE identity_ciphertext IS NOT NULL)
    OR EXISTS (SELECT 1 FROM guardian_students WHERE verification_evidence_ciphertext IS NOT NULL OR revoked_at IS NOT NULL)
    OR EXISTS (SELECT 1 FROM safety_events WHERE request_id IS NOT NULL) THEN
    RAISE EXCEPTION 'Downgrade would discard module 2 evidence or PII; use a controlled restore instead';
  END IF;
END $$;
DROP TRIGGER t10_consent_guard ON consent_records;
DROP TRIGGER t05_consent_immutable ON consent_records;
DROP TRIGGER t10_guardian_link ON guardian_students;
DROP TABLE student_assents;
DROP FUNCTION edu_append_only();
DROP FUNCTION edu_check_assent();
DROP FUNCTION edu_guard_guardian_link();
ALTER TABLE consent_records DROP COLUMN event_type, DROP COLUMN recorded_by, DROP COLUMN supersedes_id, DROP COLUMN revision;
ALTER TABLE users DROP COLUMN auth_version;
ALTER TABLE students DROP COLUMN identity_ciphertext;
ALTER TABLE guardian_students DROP COLUMN verified_by, DROP COLUMN verification_evidence_ciphertext, DROP COLUMN revoked_at;
ALTER TABLE safety_events DROP COLUMN request_id, DROP COLUMN student_id;
ALTER TABLE user_roles DROP CONSTRAINT ck_user_roles_role_values;
DO $$ DECLARE scope_id uuid; BEGIN
  FOR scope_id IN SELECT DISTINCT tenant_id FROM schools LOOP
    PERFORM set_config('app.tenant_id', scope_id::text, true);
    UPDATE user_roles SET role=CASE role WHEN 'parent' THEN 'guardian' WHEN 'content_creator' THEN 'moderator' WHEN 'sys_admin' THEN 'tenant_admin' ELSE role END;
  END LOOP;
END $$;
ALTER TABLE user_roles ADD CONSTRAINT ck_user_roles_role_values CHECK (role IN ('student','guardian','teacher','school_admin','moderator','tenant_admin'));
ALTER TABLE schools DROP CONSTRAINT uq_schools_tenant_id;
ALTER TABLE schools DROP CONSTRAINT ck_schools_school_is_tenant;
REVOKE SELECT ON schools FROM edu_auth,edu_user,edu_safety;
REVOKE INSERT ON tenants,schools FROM edu_user;
REVOKE SELECT (id,tenant_id,status,deleted_at) ON users FROM edu_safety;
REVOKE SELECT ON user_roles,students,guardians,guardian_students,teachers,teacher_classes,enrollments,classes,consent_records FROM edu_safety;
REVOKE SELECT ON classes,enrollments,teacher_classes FROM edu_user;
GRANT UPDATE ON consent_records TO edu_user;
GRANT DELETE ON guardian_students TO edu_user;
ALTER TABLE schools ENABLE ROW LEVEL SECURITY;
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE guardian_students ENABLE ROW LEVEL SECURITY;
ALTER TABLE consent_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE safety_events ENABLE ROW LEVEL SECURITY;
SELECT set_config('app.tenant_id','',true);
