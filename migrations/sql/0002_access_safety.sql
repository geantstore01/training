-- Le module 1 est conservé. Refus explicite d'une conversion ambiguë d'un tenant multi-écoles.
ALTER TABLE schools DISABLE ROW LEVEL SECURITY;
ALTER TABLE tenants DISABLE ROW LEVEL SECURITY;
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM tenants t LEFT JOIN schools s ON s.tenant_id=t.id WHERE s.id IS NULL) THEN
    RAISE EXCEPTION 'Every existing tenant needs an explicit school mapping before module 2';
  END IF;
  IF EXISTS (SELECT 1 FROM schools WHERE id <> tenant_id) THEN
    RAISE EXCEPTION 'School IDs must equal tenant IDs before module 2; migrate existing school mappings explicitly';
  END IF;
END $$;
ALTER TABLE schools ADD CONSTRAINT uq_schools_tenant_id UNIQUE (tenant_id);
ALTER TABLE schools ADD CONSTRAINT ck_schools_school_is_tenant CHECK (id = tenant_id);
ALTER TABLE users ADD COLUMN auth_version integer NOT NULL DEFAULT 1;
ALTER TABLE users ADD CONSTRAINT ck_users_auth_version_positive CHECK (auth_version > 0);
ALTER TABLE students ADD COLUMN identity_ciphertext bytea;
ALTER TABLE guardian_students ADD COLUMN verified_by uuid;
ALTER TABLE guardian_students ADD COLUMN verification_evidence_ciphertext bytea;
ALTER TABLE guardian_students ADD COLUMN revoked_at timestamptz;
ALTER TABLE guardian_students ADD CONSTRAINT fk_guardian_students_tenant_id_users FOREIGN KEY (tenant_id, verified_by) REFERENCES users (tenant_id, id) ON DELETE RESTRICT;
ALTER TABLE guardian_students ADD CONSTRAINT ck_guardian_students_revocation_order CHECK (revoked_at IS NULL OR (authority_verified_at IS NOT NULL AND revoked_at >= authority_verified_at));
ALTER TABLE safety_events ADD COLUMN request_id uuid;
ALTER TABLE safety_events ADD COLUMN student_id uuid;
ALTER TABLE safety_events ADD CONSTRAINT fk_safety_events_tenant_id_students FOREIGN KEY (tenant_id, student_id) REFERENCES students (tenant_id, id) ON DELETE RESTRICT;

-- La migration s'exécute sous RLS forcée : traiter explicitement chaque tenant.
ALTER TABLE user_roles DROP CONSTRAINT ck_user_roles_role_values;
DO $$ DECLARE scope_id uuid; BEGIN
  FOR scope_id IN SELECT DISTINCT tenant_id FROM schools LOOP
    PERFORM set_config('app.tenant_id', scope_id::text, true);
    UPDATE user_roles SET role = CASE role WHEN 'guardian' THEN 'parent' WHEN 'moderator' THEN 'content_creator' WHEN 'tenant_admin' THEN 'sys_admin' ELSE role END;
  END LOOP;
END $$;
ALTER TABLE user_roles ADD CONSTRAINT ck_user_roles_role_values CHECK (role IN ('student','parent','teacher','school_admin','content_creator','sys_admin'));

ALTER TABLE consent_records ADD COLUMN event_type varchar(20) NOT NULL DEFAULT 'legacy';
ALTER TABLE consent_records ADD COLUMN recorded_by uuid;
ALTER TABLE consent_records ADD COLUMN supersedes_id uuid;
ALTER TABLE consent_records ADD COLUMN revision integer NOT NULL DEFAULT 1;
DROP TRIGGER t10_consent_guard ON consent_records;
-- Backfill d'historique, sans modifier les preuves ni leur chronologie.
DO $$ DECLARE scope_id uuid; BEGIN
  FOR scope_id IN SELECT DISTINCT tenant_id FROM schools LOOP
    PERFORM set_config('app.tenant_id', scope_id::text, true);
    WITH ranked AS (
      SELECT id, row_number() OVER (PARTITION BY tenant_id,student_id,guardian_id,purpose ORDER BY recorded_at,id) AS n,
        lag(id) OVER (PARTITION BY tenant_id,student_id,guardian_id,purpose ORDER BY recorded_at,id) AS previous
      FROM consent_records
    ) UPDATE consent_records c SET revision=r.n, supersedes_id=r.previous FROM ranked r WHERE c.id=r.id;
  END LOOP;
END $$;
ALTER TABLE consent_records ADD CONSTRAINT fk_consent_records_tenant_id_users FOREIGN KEY (tenant_id,recorded_by) REFERENCES users(tenant_id,id) ON DELETE RESTRICT;
ALTER TABLE consent_records ADD CONSTRAINT fk_consent_records_tenant_id_consent_records FOREIGN KEY (tenant_id,supersedes_id) REFERENCES consent_records(tenant_id,id) ON DELETE RESTRICT;
ALTER TABLE consent_records ADD CONSTRAINT ck_consent_records_event_type_values CHECK (event_type IN ('legacy','grant','refuse','withdraw'));
ALTER TABLE consent_records ADD CONSTRAINT ck_consent_records_revision_positive CHECK (revision > 0);
ALTER TABLE consent_records ADD CONSTRAINT ck_consent_records_event_consistency CHECK (event_type='legacy' OR (recorded_by IS NOT NULL AND withdrawn_at IS NULL AND legal_basis='consent' AND granted=(event_type='grant')));
ALTER TABLE consent_records ADD CONSTRAINT uq_consent_stream_revision UNIQUE (tenant_id,student_id,guardian_id,purpose,revision);

CREATE TABLE student_assents (
  student_id uuid NOT NULL, recorded_by uuid NOT NULL, purpose varchar(80) NOT NULL,
  policy_version varchar(40) NOT NULL, agreed boolean NOT NULL,
  recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(), tenant_id uuid NOT NULL,
  id uuid CONSTRAINT pk_student_assents PRIMARY KEY DEFAULT gen_random_uuid(), created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_student_assents_tenant_id_id UNIQUE (tenant_id,id),
  CONSTRAINT fk_student_assents_tenant_id_students FOREIGN KEY (tenant_id,student_id) REFERENCES students(tenant_id,id) ON DELETE RESTRICT,
  CONSTRAINT fk_student_assents_tenant_id_users FOREIGN KEY (tenant_id,recorded_by) REFERENCES users(tenant_id,id) ON DELETE RESTRICT,
  CONSTRAINT fk_student_assents_tenant_id_tenants FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT
);
CREATE INDEX ix_student_assents_tenant_id ON student_assents(tenant_id);
CREATE INDEX ix_assent_lookup ON student_assents(tenant_id,student_id,purpose,recorded_at);
ALTER TABLE student_assents ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_assents FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON student_assents USING (tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid) WITH CHECK (tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid);

CREATE OR REPLACE FUNCTION edu_check_consent() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE previous consent_records%ROWTYPE;
BEGIN
  IF NEW.event_type='legacy' THEN RAISE EXCEPTION 'Legacy consent insertion forbidden' USING ERRCODE='23514'; END IF;
  IF NOT EXISTS (SELECT 1 FROM guardian_students gs JOIN guardians g ON (g.tenant_id,g.id)=(gs.tenant_id,gs.guardian_id)
    JOIN users u ON (u.tenant_id,u.id)=(g.tenant_id,g.user_id)
    JOIN user_roles r ON (r.tenant_id,r.user_id)=(u.tenant_id,u.id)
    WHERE gs.tenant_id=NEW.tenant_id AND gs.guardian_id=NEW.guardian_id AND gs.student_id=NEW.student_id
    AND gs.authority_verified_at IS NOT NULL AND gs.revoked_at IS NULL AND g.verified_at IS NOT NULL
    AND u.id=NEW.recorded_by AND u.status='active' AND r.role='parent') THEN
    RAISE EXCEPTION 'Verified parent author required' USING ERRCODE='23514';
  END IF;
  PERFORM pg_advisory_xact_lock(hashtextextended(NEW.tenant_id::text||NEW.student_id::text||NEW.guardian_id::text||NEW.purpose,0));
  SELECT * INTO previous FROM consent_records WHERE tenant_id=NEW.tenant_id AND student_id=NEW.student_id
    AND guardian_id=NEW.guardian_id AND purpose=NEW.purpose ORDER BY revision DESC LIMIT 1;
  IF NEW.event_type='withdraw' AND (previous.id IS NULL OR NOT previous.granted OR previous.withdrawn_at IS NOT NULL) THEN
    RAISE EXCEPTION 'No current grant to withdraw' USING ERRCODE='23514';
  END IF;
  NEW.revision=COALESCE(previous.revision,0)+1;
  NEW.supersedes_id=previous.id;
  NEW.recorded_at=clock_timestamp();
  RETURN NEW;
END $$;
CREATE TRIGGER t10_consent_guard BEFORE INSERT ON consent_records FOR EACH ROW EXECUTE FUNCTION edu_check_consent();
CREATE FUNCTION edu_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Append-only register' USING ERRCODE='23514'; END $$;
CREATE TRIGGER t05_consent_immutable BEFORE UPDATE OR DELETE ON consent_records FOR EACH ROW EXECUTE FUNCTION edu_append_only();
CREATE TRIGGER t05_assent_immutable BEFORE UPDATE OR DELETE ON student_assents FOR EACH ROW EXECUTE FUNCTION edu_append_only();
CREATE FUNCTION edu_check_assent() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM students s JOIN users u ON (u.tenant_id,u.id)=(s.tenant_id,s.user_id)
      WHERE s.tenant_id=NEW.tenant_id AND s.id=NEW.student_id AND s.user_id=NEW.recorded_by AND u.status='active') THEN
    RAISE EXCEPTION 'Student author required' USING ERRCODE='23514';
  END IF;
  NEW.recorded_at=clock_timestamp(); RETURN NEW;
END $$;
CREATE TRIGGER t10_assent_guard BEFORE INSERT ON student_assents FOR EACH ROW EXECUTE FUNCTION edu_check_assent();

CREATE FUNCTION edu_guard_guardian_link() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.authority_verified_at IS NOT NULL AND (
    (to_jsonb(OLD)-ARRAY['revoked_at','updated_at']) IS DISTINCT FROM (to_jsonb(NEW)-ARRAY['revoked_at','updated_at'])
    OR OLD.revoked_at IS NOT NULL) THEN
    RAISE EXCEPTION 'Verified guardian link immutable except first revocation' USING ERRCODE='23514';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER t10_guardian_link BEFORE UPDATE ON guardian_students FOR EACH ROW EXECUTE FUNCTION edu_guard_guardian_link();

-- Adapter la validation indépendante aux six rôles, sans autoriser l'auto-approbation.
DO $$ DECLARE definition text; BEGIN
  SELECT pg_get_functiondef('edu_guard_review()'::regprocedure) INTO definition;
  definition=replace(definition, '''teacher'',''moderator'',''tenant_admin''', '''teacher'',''school_admin'',''sys_admin''');
  EXECUTE definition;
END $$;

GRANT SELECT ON schools TO edu_auth, edu_safety;
GRANT SELECT (id,tenant_id,status,auth_version,deleted_at) ON users TO edu_safety;
GRANT SELECT ON user_roles, students, guardians, guardian_students, teachers, teacher_classes,
  enrollments, classes, consent_records, student_assents TO edu_safety;
GRANT SELECT ON classes, enrollments, teacher_classes TO edu_user;
GRANT INSERT ON tenants, schools TO edu_user;
GRANT SELECT ON schools TO edu_user;
GRANT SELECT, INSERT ON student_assents TO edu_user;
REVOKE UPDATE ON consent_records FROM edu_user;
REVOKE DELETE ON guardian_students FROM edu_user;
REVOKE ALL ON FUNCTION edu_append_only(), edu_check_assent(), edu_guard_guardian_link() FROM PUBLIC;
SELECT set_config('app.tenant_id','',true);
ALTER TABLE schools ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
