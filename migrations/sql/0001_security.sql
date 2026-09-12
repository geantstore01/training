-- RLS et privilèges : aucune identité tenant par défaut.
DO $block$
DECLARE tab text;
BEGIN
  FOR tab IN SELECT table_name FROM information_schema.columns
    WHERE table_schema = 'public' AND column_name = 'tenant_id'
  LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', tab);
    EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', tab);
    EXECUTE format('CREATE POLICY tenant_isolation ON %I USING (tenant_id = NULLIF(current_setting(''app.tenant_id'', true), '''')::uuid) WITH CHECK (tenant_id = NULLIF(current_setting(''app.tenant_id'', true), '''')::uuid)', tab);
  END LOOP;
END $block$;
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenants FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON tenants
  USING (id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
  WITH CHECK (id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);

CREATE FUNCTION edu_touch_updated_at() RETURNS trigger LANGUAGE plpgsql AS $fn$
BEGIN
  NEW.updated_at = clock_timestamp();
  RETURN NEW;
END $fn$;
DO $block$
DECLARE tab text;
BEGIN
  FOR tab IN SELECT table_name FROM information_schema.columns
    WHERE table_schema = 'public' AND column_name = 'updated_at'
  LOOP
    EXECUTE format('CREATE TRIGGER t90_updated_at BEFORE UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION edu_touch_updated_at()', tab);
  END LOOP;
END $block$;

CREATE FUNCTION edu_check_prerequisite_cycle() RETURNS trigger LANGUAGE plpgsql AS $fn$
BEGIN
  PERFORM pg_advisory_xact_lock(731241002);
  IF EXISTS (
    WITH RECURSIVE ancestors(id) AS (
      SELECT NEW.prerequisite_id
      UNION
      SELECT p.prerequisite_id FROM competency_prerequisites p JOIN ancestors a ON p.competency_id = a.id WHERE p.id <> NEW.id
    ) SELECT 1 FROM ancestors WHERE id = NEW.competency_id
  ) THEN RAISE EXCEPTION 'Competency prerequisite cycle' USING ERRCODE = '23514'; END IF;
  RETURN NEW;
END $fn$;
CREATE TRIGGER t10_prerequisite_cycle BEFORE INSERT OR UPDATE ON competency_prerequisites
  FOR EACH ROW EXECUTE FUNCTION edu_check_prerequisite_cycle();

CREATE FUNCTION edu_guard_version() RETURNS trigger LANGUAGE plpgsql AS $fn$
DECLARE approved boolean;
BEGIN
  IF TG_OP = 'INSERT' THEN
    IF NEW.status <> 'draft' THEN RAISE EXCEPTION 'New version must be draft' USING ERRCODE = '23514'; END IF;
    RETURN NEW;
  END IF;
  IF OLD.status <> 'draft' AND
    (to_jsonb(NEW) - ARRAY['status','published_at','updated_at']) IS DISTINCT FROM
    (to_jsonb(OLD) - ARRAY['status','published_at','updated_at']) THEN
    RAISE EXCEPTION 'Reviewed version is immutable; create a new version' USING ERRCODE = '23514';
  END IF;
  IF OLD.status IN ('published','retired') AND
    (NEW.published_at IS DISTINCT FROM OLD.published_at OR
      (NEW.status <> OLD.status AND NOT (OLD.status = 'published' AND NEW.status = 'retired'))) THEN
    RAISE EXCEPTION 'Invalid published version transition' USING ERRCODE = '23514';
  END IF;
  IF NEW.status = 'retired' AND OLD.status NOT IN ('published','retired') THEN
    RAISE EXCEPTION 'Only published content can be retired' USING ERRCODE = '23514';
  END IF;
  IF NEW.status = 'published' AND OLD.status <> 'published' THEN
    IF OLD.status <> 'in_review' THEN RAISE EXCEPTION 'Review required' USING ERRCODE = '23514'; END IF;
    IF TG_TABLE_NAME = 'lesson_versions' THEN
      SELECT decision = 'approved' AND reviewed_at >= OLD.updated_at INTO approved
        FROM content_reviews WHERE tenant_id = NEW.tenant_id AND lesson_version_id = NEW.id ORDER BY reviewed_at DESC, id DESC LIMIT 1;
    ELSE
      SELECT decision = 'approved' AND reviewed_at >= OLD.updated_at INTO approved
        FROM content_reviews WHERE tenant_id = NEW.tenant_id AND exercise_version_id = NEW.id ORDER BY reviewed_at DESC, id DESC LIMIT 1;
    END IF;
    IF approved IS DISTINCT FROM true THEN RAISE EXCEPTION 'Current human approval required' USING ERRCODE = '23514'; END IF;
  END IF;
  RETURN NEW;
END $fn$;
CREATE TRIGGER t10_version_guard BEFORE INSERT OR UPDATE ON lesson_versions FOR EACH ROW EXECUTE FUNCTION edu_guard_version();
CREATE TRIGGER t10_version_guard BEFORE INSERT OR UPDATE ON exercise_versions FOR EACH ROW EXECUTE FUNCTION edu_guard_version();

CREATE FUNCTION edu_guard_review() RETURNS trigger LANGUAGE plpgsql AS $fn$
DECLARE author uuid; state text;
BEGIN
  IF NEW.lesson_version_id IS NOT NULL THEN
    SELECT l.author_id, v.status INTO author, state FROM lesson_versions v JOIN lessons l
      ON (l.tenant_id, l.id) = (v.tenant_id, v.lesson_id)
      WHERE v.tenant_id = NEW.tenant_id AND v.id = NEW.lesson_version_id FOR UPDATE OF v;
  ELSE
    SELECT e.author_id, v.status INTO author, state FROM exercise_versions v JOIN exercises e
      ON (e.tenant_id, e.id) = (v.tenant_id, v.exercise_id)
      WHERE v.tenant_id = NEW.tenant_id AND v.id = NEW.exercise_version_id FOR UPDATE OF v;
  END IF;
  IF state IS DISTINCT FROM 'in_review' OR author = NEW.reviewer_id THEN
    RAISE EXCEPTION 'Independent human review of in-review content required' USING ERRCODE = '23514';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM user_roles r JOIN users u ON (u.tenant_id,u.id)=(r.tenant_id,r.user_id)
    WHERE r.tenant_id = NEW.tenant_id AND r.user_id = NEW.reviewer_id
    AND r.role IN ('teacher','moderator','tenant_admin') AND u.status='active') THEN
    RAISE EXCEPTION 'Reviewer role required' USING ERRCODE = '23514';
  END IF;
  NEW.reviewed_at = clock_timestamp();
  RETURN NEW;
END $fn$;
CREATE TRIGGER t10_review_guard BEFORE INSERT ON content_reviews FOR EACH ROW EXECUTE FUNCTION edu_guard_review();

CREATE FUNCTION edu_guard_version_child() RETURNS trigger LANGUAGE plpgsql AS $fn$
DECLARE row_data jsonb; state text; version_id uuid; scope_id uuid; previous jsonb;
BEGIN
  row_data = CASE WHEN TG_OP = 'DELETE' THEN to_jsonb(OLD) ELSE to_jsonb(NEW) END;
  previous = CASE WHEN TG_OP = 'UPDATE' THEN to_jsonb(OLD) ELSE row_data END;
  -- Vérifie aussi l'ancien parent afin d'interdire le déplacement d'un indice publié.
  FOR row_data IN SELECT previous UNION SELECT row_data LOOP
    scope_id = (row_data->>'tenant_id')::uuid;
    IF TG_TABLE_NAME IN ('lesson_competencies','lesson_sources') THEN
      version_id = (row_data->>'lesson_version_id')::uuid;
      SELECT status INTO state FROM lesson_versions WHERE tenant_id=scope_id AND id=version_id FOR UPDATE;
    ELSE
      version_id = (row_data->>'exercise_version_id')::uuid;
      SELECT status INTO state FROM exercise_versions WHERE tenant_id=scope_id AND id=version_id FOR UPDATE;
    END IF;
    IF state IS DISTINCT FROM 'draft' THEN RAISE EXCEPTION 'Version children are immutable after submission' USING ERRCODE = '23514'; END IF;
  END LOOP;
  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END $fn$;
DO $block$
DECLARE tab text;
BEGIN
  FOREACH tab IN ARRAY ARRAY['hints','lesson_competencies','exercise_competencies','lesson_sources','exercise_sources'] LOOP
    EXECUTE format('CREATE TRIGGER t10_child_guard BEFORE INSERT OR UPDATE OR DELETE ON %I FOR EACH ROW EXECUTE FUNCTION edu_guard_version_child()', tab);
  END LOOP;
END $block$;

CREATE FUNCTION edu_check_consent() RETURNS trigger LANGUAGE plpgsql AS $fn$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM guardian_students gs JOIN guardians g ON (g.tenant_id,g.id)=(gs.tenant_id,gs.guardian_id)
    WHERE gs.tenant_id=NEW.tenant_id AND gs.guardian_id=NEW.guardian_id AND gs.student_id=NEW.student_id
    AND gs.authority_verified_at IS NOT NULL AND g.verified_at IS NOT NULL) THEN
    RAISE EXCEPTION 'Verified guardian authority required' USING ERRCODE='23514';
  END IF;
  IF TG_OP='UPDATE' AND ((to_jsonb(NEW)-ARRAY['withdrawn_at','updated_at']) IS DISTINCT FROM
      (to_jsonb(OLD)-ARRAY['withdrawn_at','updated_at']) OR OLD.withdrawn_at IS NOT NULL) THEN
    RAISE EXCEPTION 'Consent evidence is immutable; append a new record' USING ERRCODE='23514';
  END IF;
  RETURN NEW;
END $fn$;
CREATE TRIGGER t10_consent_guard BEFORE INSERT OR UPDATE ON consent_records FOR EACH ROW EXECUTE FUNCTION edu_check_consent();

CREATE FUNCTION edu_check_attempt() RETURNS trigger LANGUAGE plpgsql AS $fn$
DECLARE version_state text;
BEGIN
  SELECT status INTO version_state FROM exercise_versions WHERE tenant_id=NEW.tenant_id AND id=NEW.exercise_version_id;
  IF version_state IS DISTINCT FROM 'published' THEN
    RAISE EXCEPTION 'Only published exercises can be attempted' USING ERRCODE='23514';
  END IF;
  RETURN NEW;
END $fn$;
CREATE TRIGGER t10_attempt_guard BEFORE INSERT OR UPDATE OF exercise_version_id ON exercise_attempts FOR EACH ROW EXECUTE FUNCTION edu_check_attempt();

-- Le rôle partagé ne reçoit que le référentiel pédagogique public et non personnel.
GRANT SELECT ON subjects, curriculum_levels, competencies, competency_prerequisites TO edu_runtime;
GRANT SELECT ON tenants TO edu_runtime;
GRANT SELECT, INSERT, UPDATE ON users TO edu_auth;
GRANT SELECT ON user_roles TO edu_auth;
GRANT SELECT, INSERT, UPDATE, DELETE ON users, user_roles, guardians, students, guardian_students, teachers TO edu_user;
GRANT SELECT, INSERT, UPDATE ON consent_records TO edu_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON schools, classes, enrollments, teacher_classes, learning_groups, group_members TO edu_class;
GRANT SELECT ON students, teachers TO edu_class;
GRANT INSERT, UPDATE, DELETE ON subjects, curriculum_levels, competencies, competency_prerequisites TO edu_curriculum;
GRANT SELECT, INSERT, UPDATE ON lessons, lesson_versions, lesson_competencies, lesson_sources TO edu_content;
GRANT SELECT ON users, content_reviews, content_sources TO edu_content;
GRANT SELECT, INSERT, UPDATE ON exercises, exercise_versions, exercise_competencies, exercise_sources, hints TO edu_exercise;
GRANT SELECT ON users, content_reviews, content_sources TO edu_exercise;
GRANT SELECT, INSERT, UPDATE, DELETE ON learning_sessions, exercise_attempts, answers, mastery_records, spaced_repetition_items TO edu_assessment;
GRANT SELECT ON students, exercise_versions, exercise_competencies TO edu_assessment;
GRANT SELECT ON students, learning_sessions, mastery_records, lesson_versions, lesson_competencies, hints TO edu_tutor;
GRANT SELECT (tenant_id, id, exercise_id, version, kind, prompt, difficulty, status, published_at, created_at, updated_at) ON exercise_versions TO edu_tutor;
GRANT SELECT, INSERT ON ai_interactions TO edu_tutor, edu_ai_router;
GRANT SELECT, INSERT, UPDATE, DELETE ON content_chunks TO edu_retrieval;
GRANT SELECT ON content_sources TO edu_retrieval;
GRANT SELECT ON consent_records, guardians, guardian_students, students, mastery_records TO edu_notification;
GRANT SELECT ON mastery_records, exercise_attempts, learning_sessions TO edu_analytics;
GRANT SELECT, INSERT ON content_reviews TO edu_admin;
GRANT SELECT ON users, user_roles, lessons, lesson_versions, exercises, exercise_versions, safety_events TO edu_admin;
GRANT UPDATE (status, published_at) ON lesson_versions, exercise_versions TO edu_admin;
GRANT SELECT, INSERT, UPDATE ON content_sources TO edu_admin;
GRANT SELECT, INSERT ON safety_events TO edu_safety;
GRANT SELECT ON ai_interactions TO edu_safety;
GRANT INSERT ON audit_logs TO edu_runtime;
GRANT SELECT ON audit_logs TO edu_admin;
-- Pas de droits TRUNCATE, DDL, BYPASSRLS ou de modification des audits/reviews.
REVOKE ALL ON FUNCTION edu_touch_updated_at(), edu_check_prerequisite_cycle(), edu_guard_version(),
 edu_guard_review(), edu_guard_version_child(), edu_check_consent(), edu_check_attempt() FROM PUBLIC;

INSERT INTO curriculum_levels (id, code, cycle) VALUES
 ('00000000-0000-0000-0000-000000000101', 'CM1', 3),
 ('00000000-0000-0000-0000-000000000102', 'CM2', 3);
-- Aucun programme ni cours fabriqué : l'import référencé sera livré avec curriculum-service.
