
CREATE TABLE curriculum_domains (
	subject_id UUID NOT NULL, 
	code VARCHAR(80) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_curriculum_domains PRIMARY KEY (id), 
	CONSTRAINT uq_curriculum_domains_subject_id_code UNIQUE (subject_id, code), 
	CONSTRAINT uq_curriculum_domains_id_subject_id UNIQUE (id, subject_id), 
	CONSTRAINT fk_curriculum_domains_subject_id_subjects FOREIGN KEY(subject_id) REFERENCES subjects (id)
)

;

CREATE TRIGGER t90_updated_at BEFORE UPDATE ON curriculum_domains FOR EACH ROW EXECUTE FUNCTION edu_touch_updated_at();
ALTER TABLE competencies ADD COLUMN domain_id uuid,
 ADD COLUMN objectives jsonb NOT NULL DEFAULT '[]'::jsonb,
 ADD COLUMN common_errors jsonb NOT NULL DEFAULT '[]'::jsonb,
 ADD CONSTRAINT fk_competencies_domain_id_curriculum_domains FOREIGN KEY(domain_id,subject_id) REFERENCES curriculum_domains(id,subject_id),
 ADD CONSTRAINT ck_competencies_pedagogy_arrays CHECK(jsonb_typeof(objectives)='array' AND jsonb_typeof(common_errors)='array');
ALTER TABLE lessons ADD COLUMN kind varchar(30) NOT NULL DEFAULT 'lesson',
 ADD CONSTRAINT ck_lessons_kind_values CHECK(kind IN ('lesson','teaching_sheet','learning_sequence'));
ALTER TABLE lesson_versions ADD COLUMN editor_id uuid,
 ADD COLUMN review_round integer NOT NULL DEFAULT 0,
 ADD CONSTRAINT fk_lesson_versions_tenant_id_users FOREIGN KEY(tenant_id,editor_id) REFERENCES users(tenant_id,id) ON DELETE RESTRICT,
 ADD CONSTRAINT ck_lesson_versions_review_round_positive CHECK(review_round >= 0);
ALTER TABLE content_reviews ADD COLUMN review_round integer;
ALTER TABLE mastery_records ADD COLUMN evaluation_level varchar(20) NOT NULL DEFAULT 'non_evalué',
 ADD CONSTRAINT ck_mastery_records_evaluation_level_values CHECK(evaluation_level IN ('non_evalué','découverte','en_cours','fragile','maîtrisé','consolidé'));
DROP TRIGGER t10_version_guard ON lesson_versions;
ALTER TABLE lesson_versions DROP CONSTRAINT ck_lesson_versions_status_values,
 DROP CONSTRAINT ck_lesson_versions_publication_date;
-- Owner uses a brief transactional RLS suspension under DDL locks for global backfill.
ALTER TABLE lesson_versions DISABLE ROW LEVEL SECURITY;
ALTER TABLE lessons DISABLE ROW LEVEL SECURITY;
UPDATE lesson_versions v SET editor_id=l.author_id FROM lessons l WHERE (l.tenant_id,l.id)=(v.tenant_id,v.lesson_id);
UPDATE lesson_versions SET status=CASE status WHEN 'in_review' THEN 'pending_review' WHEN 'published' THEN 'approved' WHEN 'retired' THEN 'archived' ELSE status END;
-- Keep already published records; ambiguous multiple-current publications require operator correction.
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM lesson_versions WHERE status='approved' GROUP BY tenant_id,lesson_id HAVING count(*)>1) THEN
  RAISE EXCEPTION 'Multiple published versions: archive old versions before migration' USING ERRCODE='23514';
 END IF;
END $$;
ALTER TABLE lesson_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE lessons ENABLE ROW LEVEL SECURITY;
ALTER TABLE lesson_versions ADD CONSTRAINT ck_lesson_versions_status_values CHECK(status IN ('draft','pending_review','approved','archived')),
 ADD CONSTRAINT ck_lesson_versions_publication_date CHECK((status='approved' AND published_at IS NOT NULL) OR (status IN ('draft','pending_review') AND published_at IS NULL) OR status='archived');
CREATE UNIQUE INDEX uq_lesson_one_approved ON lesson_versions(tenant_id,lesson_id) WHERE status='approved';

CREATE FUNCTION edu_guard_lesson_version() RETURNS trigger LANGUAGE plpgsql AS $fn$
DECLARE accepted boolean;
BEGIN
 IF TG_OP='INSERT' THEN
  IF NEW.status<>'draft' OR NEW.published_at IS NOT NULL OR NEW.review_round<>0 THEN
   RAISE EXCEPTION 'New content must be draft' USING ERRCODE='23514';
  END IF;
  RETURN NEW;
 END IF;
 IF (to_jsonb(NEW)-ARRAY['status','published_at','updated_at','review_round']) IS DISTINCT FROM
    (to_jsonb(OLD)-ARRAY['status','published_at','updated_at','review_round']) THEN
  RAISE EXCEPTION 'Content snapshot is immutable: create a new version' USING ERRCODE='23514';
 END IF;
 IF NEW.review_round<>OLD.review_round OR NEW.published_at IS DISTINCT FROM OLD.published_at THEN
  RAISE EXCEPTION 'Server-managed review/publication fields' USING ERRCODE='23514';
 END IF;
 IF NEW.status=OLD.status THEN RETURN NEW; END IF;
 IF OLD.status='archived' OR NOT (
  (OLD.status='draft' AND NEW.status IN ('pending_review','archived')) OR
  (OLD.status='pending_review' AND NEW.status IN ('draft','approved','archived')) OR
  (OLD.status='approved' AND NEW.status='archived')) THEN
  RAISE EXCEPTION 'Invalid content transition' USING ERRCODE='23514';
 END IF;
 IF NEW.status='pending_review' THEN
  NEW.review_round=OLD.review_round+1;
 ELSIF NEW.status IN ('approved','draft') AND OLD.status='pending_review' THEN
  SELECT CASE WHEN NEW.status='approved' THEN decision='approved' ELSE decision IN ('rejected','changes_requested') END INTO accepted
   FROM content_reviews WHERE tenant_id=NEW.tenant_id AND lesson_version_id=NEW.id AND review_round=OLD.review_round
   ORDER BY reviewed_at DESC,id DESC LIMIT 1;
  IF accepted IS DISTINCT FROM true THEN RAISE EXCEPTION 'Current independent review required' USING ERRCODE='23514'; END IF;
  IF NEW.status='approved' THEN NEW.published_at=clock_timestamp(); END IF;
 END IF;
 RETURN NEW;
END $fn$;
CREATE TRIGGER t10_version_guard BEFORE INSERT OR UPDATE ON lesson_versions FOR EACH ROW EXECUTE FUNCTION edu_guard_lesson_version();

CREATE OR REPLACE FUNCTION edu_guard_review() RETURNS trigger LANGUAGE plpgsql AS $fn$
DECLARE author uuid; editor uuid; state text; round integer;
BEGIN
 IF NEW.lesson_version_id IS NOT NULL THEN
  SELECT l.author_id,v.editor_id,v.status,v.review_round INTO author,editor,state,round
   FROM lesson_versions v JOIN lessons l ON (l.tenant_id,l.id)=(v.tenant_id,v.lesson_id)
   WHERE v.tenant_id=NEW.tenant_id AND v.id=NEW.lesson_version_id FOR UPDATE OF v;
  IF state IS DISTINCT FROM 'pending_review' OR NEW.reviewer_id IN (author,editor) THEN
   RAISE EXCEPTION 'Independent review of pending version required' USING ERRCODE='23514';
  END IF;
  NEW.review_round=round;
 ELSE
  SELECT e.author_id,v.status INTO author,state FROM exercise_versions v JOIN exercises e
   ON (e.tenant_id,e.id)=(v.tenant_id,v.exercise_id)
   WHERE v.tenant_id=NEW.tenant_id AND v.id=NEW.exercise_version_id FOR UPDATE OF v;
  IF state IS DISTINCT FROM 'in_review' OR author=NEW.reviewer_id THEN
   RAISE EXCEPTION 'Independent exercise review required' USING ERRCODE='23514';
  END IF;
 END IF;
 IF NOT EXISTS(SELECT 1 FROM user_roles r JOIN users u ON (u.tenant_id,u.id)=(r.tenant_id,r.user_id)
  WHERE r.tenant_id=NEW.tenant_id AND r.user_id=NEW.reviewer_id AND u.status='active' AND u.deleted_at IS NULL
  AND ((NEW.lesson_version_id IS NOT NULL AND r.role IN ('teacher','content_creator')) OR
       (NEW.exercise_version_id IS NOT NULL AND r.role IN ('teacher','school_admin','sys_admin')))) THEN
  RAISE EXCEPTION 'Qualified reviewer required' USING ERRCODE='23514';
 END IF;
 NEW.reviewed_at=clock_timestamp();
 RETURN NEW;
END $fn$;
CREATE FUNCTION edu_immutable_content_record() RETURNS trigger LANGUAGE plpgsql AS $fn$
BEGIN RAISE EXCEPTION 'Immutable editorial record' USING ERRCODE='23514'; END $fn$;
CREATE TRIGGER t05_immutable BEFORE UPDATE OR DELETE ON lessons FOR EACH ROW EXECUTE FUNCTION edu_immutable_content_record();
CREATE TRIGGER t05_immutable BEFORE UPDATE OR DELETE ON content_reviews FOR EACH ROW EXECUTE FUNCTION edu_immutable_content_record();
CREATE TRIGGER t05_immutable BEFORE UPDATE OR DELETE ON lesson_competencies FOR EACH ROW EXECUTE FUNCTION edu_immutable_content_record();
CREATE TRIGGER t05_immutable BEFORE UPDATE OR DELETE ON lesson_sources FOR EACH ROW EXECUTE FUNCTION edu_immutable_content_record();
GRANT SELECT ON curriculum_domains TO edu_runtime;
GRANT INSERT ON curriculum_domains TO edu_curriculum;
GRANT SELECT ON schools,user_roles TO edu_curriculum,edu_content;
GRANT SELECT(id,tenant_id,status,auth_version,deleted_at) ON users TO edu_curriculum;
GRANT SELECT ON students,guardians,guardian_students,teachers,teacher_classes,enrollments,mastery_records TO edu_curriculum;
GRANT INSERT ON content_reviews,content_sources TO edu_content;
REVOKE ALL ON FUNCTION edu_guard_lesson_version(),edu_immutable_content_record() FROM PUBLIC;
INSERT INTO subjects(id,code,name) VALUES
 ('00000000-0000-0000-0000-000000000201','francais','Français'),
 ('00000000-0000-0000-0000-000000000202','mathematiques','Mathématiques'),
 ('00000000-0000-0000-0000-000000000203','histoire','Histoire') ON CONFLICT(code) DO NOTHING;
