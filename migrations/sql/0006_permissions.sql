GRANT SELECT ON schools,user_roles TO edu_class,edu_analytics,edu_admin,edu_speech,edu_notification;
GRANT SELECT(id,tenant_id,status,auth_version,deleted_at) ON users TO edu_class,edu_analytics,edu_speech,edu_notification;
GRANT SELECT ON students,guardians,guardian_students,teachers,teacher_classes,enrollments TO edu_analytics,edu_speech,edu_notification;
GRANT SELECT ON consent_records,student_assents TO edu_speech;
GRANT SELECT(id,tenant_id,status,prompt) ON exercise_versions TO edu_speech,edu_class;
GRANT SELECT ON exercise_competencies TO edu_class;
GRANT SELECT ON rag_documents TO edu_admin;
GRANT SELECT,INSERT,UPDATE ON missions TO edu_class;
GRANT SELECT,INSERT ON mission_exercises TO edu_class;
GRANT SELECT ON feature_flags TO edu_class,edu_speech,edu_notification;
GRANT SELECT,INSERT,UPDATE ON feature_flags TO edu_admin;
GRANT SELECT,INSERT ON safety_cases TO edu_admin;
GRANT SELECT,INSERT,UPDATE,DELETE ON background_jobs,job_dispatch,notifications TO edu_notification;
GRANT SELECT ON learning_sessions,exercise_attempts TO edu_notification;
GRANT SELECT,INSERT ON exercises,exercise_versions,exercise_competencies,exercise_sources,hints TO edu_notification;
GRANT SELECT ON content_sources TO edu_notification;
GRANT SELECT,DELETE ON tutor_turns,safety_events,ai_interactions,audit_logs TO edu_notification;
CREATE TRIGGER t05_immutable BEFORE UPDATE ON safety_cases FOR EACH ROW EXECUTE FUNCTION edu_immutable_content_record();
CREATE FUNCTION edu_mission_group() RETURNS trigger LANGUAGE plpgsql AS $fn$
BEGIN
 IF NEW.group_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM learning_groups WHERE id=NEW.group_id AND tenant_id=NEW.tenant_id AND class_id=NEW.class_id) THEN
  RAISE EXCEPTION 'Group belongs to another class' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $fn$;
CREATE TRIGGER t05_group BEFORE INSERT OR UPDATE ON missions FOR EACH ROW EXECUTE FUNCTION edu_mission_group();
REVOKE ALL ON FUNCTION edu_mission_group() FROM PUBLIC;
GRANT UPDATE(id) ON exercise_versions TO edu_notification;
GRANT SELECT ON classes TO edu_analytics;
