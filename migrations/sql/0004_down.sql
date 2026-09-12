ALTER TABLE exercise_versions DISABLE ROW LEVEL SECURITY;
ALTER TABLE exercise_attempts DISABLE ROW LEVEL SECURITY;
ALTER TABLE mastery_evidence DISABLE ROW LEVEL SECURITY;
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM exercise_versions WHERE validator_name='controlled' OR pipeline_report<>'[]'::jsonb OR kind IN ('fill_blanks','step_problem','timeline'))
 OR EXISTS(SELECT 1 FROM exercise_attempts WHERE submission_digest IS NOT NULL OR assessment_result IS NOT NULL)
 OR EXISTS(SELECT 1 FROM mastery_evidence) THEN
  RAISE EXCEPTION 'Module 4 data present: downgrade would lose assessment history' USING ERRCODE='23514';
 END IF;
END $$;
DROP TABLE mastery_evidence;
DROP TRIGGER t05_immutable ON exercises;
DROP TRIGGER t05_immutable ON answers;
DROP TRIGGER t05_controlled ON exercise_versions;
DROP TRIGGER t05_completed ON exercise_attempts;
DROP FUNCTION edu_controlled_exercise();
DROP FUNCTION edu_completed_attempt();
ALTER TABLE exercise_attempts DROP CONSTRAINT uq_attempt_evidence_scope,
 DROP COLUMN submission_digest,DROP COLUMN assessment_result;
ALTER TABLE exercise_versions DROP COLUMN pipeline_report;
ALTER TABLE exercise_versions DROP CONSTRAINT ck_exercise_versions_kind_values;
ALTER TABLE exercise_versions ADD CONSTRAINT ck_exercise_versions_kind_values CHECK(kind IN ('multiple_choice','integer','decimal','fraction','short_text','ordering','matching'));
ALTER TABLE exercise_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE exercise_attempts ENABLE ROW LEVEL SECURITY;
REVOKE SELECT ON schools,user_roles FROM edu_exercise,edu_assessment;
REVOKE SELECT(id,tenant_id,status,auth_version,deleted_at) ON users FROM edu_assessment;
REVOKE SELECT ON exercises,exercise_sources,hints,guardians,guardian_students,teachers,teacher_classes,enrollments FROM edu_assessment;
REVOKE INSERT ON content_reviews FROM edu_exercise;
