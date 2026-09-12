ALTER TABLE exercise_versions ADD COLUMN pipeline_report jsonb NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE exercise_versions DROP CONSTRAINT ck_exercise_versions_kind_values;
ALTER TABLE exercise_versions ADD CONSTRAINT ck_exercise_versions_kind_values CHECK(kind IN ('multiple_choice','integer','decimal','fraction','short_text','ordering','matching','fill_blanks','step_problem','timeline'));
ALTER TABLE exercise_attempts ADD COLUMN submission_digest varchar(64), ADD COLUMN assessment_result jsonb,
 ADD CONSTRAINT uq_attempt_evidence_scope UNIQUE(tenant_id,id,student_id,exercise_version_id);

CREATE TABLE mastery_evidence (
	attempt_id UUID NOT NULL, 
	student_id UUID NOT NULL, 
	exercise_version_id UUID NOT NULL, 
	competency_id UUID NOT NULL, 
	applied BOOLEAN NOT NULL, 
	correct BOOLEAN NOT NULL, 
	reason VARCHAR(30) NOT NULL, 
	probability_before NUMERIC(6, 5) NOT NULL, 
	probability_after NUMERIC(6, 5) NOT NULL, 
	algorithm_version VARCHAR(40) NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_mastery_evidence PRIMARY KEY (id), 
	CONSTRAINT fk_mastery_evidence_tenant_id_exercise_attempts FOREIGN KEY(tenant_id, attempt_id, student_id, exercise_version_id) REFERENCES exercise_attempts (tenant_id, id, student_id, exercise_version_id), 
	CONSTRAINT uq_mastery_evidence_tenant_id_attempt_id_competency_id UNIQUE (tenant_id, attempt_id, competency_id), 
	CONSTRAINT ck_mastery_evidence_probabilities CHECK (probability_before BETWEEN 0 AND 1 AND probability_after BETWEEN 0 AND 1), 
	CONSTRAINT ck_mastery_evidence_reason_values CHECK (reason IN ('independent','repeated','assisted','unrecognized')), 
	CONSTRAINT uq_mastery_evidence_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_mastery_evidence_competency_id_competencies FOREIGN KEY(competency_id) REFERENCES competencies (id), 
	CONSTRAINT fk_mastery_evidence_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;
CREATE INDEX ix_evidence_repeat ON mastery_evidence (tenant_id, student_id, competency_id, exercise_version_id, created_at);
CREATE INDEX ix_mastery_evidence_tenant_id ON mastery_evidence (tenant_id);
ALTER TABLE mastery_evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE mastery_evidence FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON mastery_evidence USING(tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid)
 WITH CHECK(tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid);
CREATE TRIGGER t90_updated_at BEFORE UPDATE ON mastery_evidence FOR EACH ROW EXECUTE FUNCTION edu_touch_updated_at();
CREATE TRIGGER t05_immutable BEFORE UPDATE OR DELETE ON mastery_evidence FOR EACH ROW EXECUTE FUNCTION edu_immutable_content_record();
CREATE TRIGGER t05_immutable BEFORE UPDATE OR DELETE ON exercises FOR EACH ROW EXECUTE FUNCTION edu_immutable_content_record();
CREATE FUNCTION edu_controlled_exercise() RETURNS trigger LANGUAGE plpgsql AS $fn$
BEGIN
 IF TG_OP='UPDATE' AND (to_jsonb(NEW)-ARRAY['status','published_at','updated_at']) IS DISTINCT FROM
  (to_jsonb(OLD)-ARRAY['status','published_at','updated_at']) THEN
  RAISE EXCEPTION 'Exercise snapshot immutable: create a new version' USING ERRCODE='23514';
 END IF;
 IF NEW.validator_name='controlled' THEN
  IF NEW.validator_version<>'controlled-v1' OR jsonb_typeof(NEW.pipeline_report)<>'array' OR jsonb_array_length(NEW.pipeline_report)<>10
   OR EXISTS(SELECT 1 FROM jsonb_array_elements(NEW.pipeline_report) x WHERE (x->>'passed') IS DISTINCT FROM 'true') THEN
   RAISE EXCEPTION 'Ten validation checks required' USING ERRCODE='23514';
  END IF;
 END IF;
 RETURN NEW;
END $fn$;
CREATE TRIGGER t05_controlled BEFORE INSERT OR UPDATE ON exercise_versions FOR EACH ROW EXECUTE FUNCTION edu_controlled_exercise();
CREATE FUNCTION edu_completed_attempt() RETURNS trigger LANGUAGE plpgsql AS $fn$
BEGIN
 IF OLD.submitted_at IS NOT NULL AND to_jsonb(NEW) IS DISTINCT FROM to_jsonb(OLD) THEN
  RAISE EXCEPTION 'Submitted attempt immutable' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $fn$;
CREATE TRIGGER t05_completed BEFORE UPDATE ON exercise_attempts FOR EACH ROW EXECUTE FUNCTION edu_completed_attempt();
CREATE TRIGGER t05_immutable BEFORE UPDATE OR DELETE ON answers FOR EACH ROW EXECUTE FUNCTION edu_immutable_content_record();
GRANT SELECT ON schools,user_roles TO edu_exercise,edu_assessment;
GRANT SELECT(id,tenant_id,status,auth_version,deleted_at) ON users TO edu_assessment;
GRANT SELECT ON exercises,exercise_sources,hints,guardians,guardian_students,teachers,teacher_classes,enrollments TO edu_assessment;
GRANT SELECT,INSERT ON mastery_evidence TO edu_assessment;
GRANT INSERT ON content_reviews TO edu_exercise;
REVOKE ALL ON FUNCTION edu_controlled_exercise(),edu_completed_attempt() FROM PUBLIC;
