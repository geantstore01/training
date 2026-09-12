
-- Refuse lossy downgrade; operator restores a backup if editorial data exists.
ALTER TABLE lesson_versions DISABLE ROW LEVEL SECURITY;
ALTER TABLE lessons DISABLE ROW LEVEL SECURITY;
ALTER TABLE mastery_records DISABLE ROW LEVEL SECURITY;
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM curriculum_domains) OR EXISTS(SELECT 1 FROM competencies WHERE domain_id IS NOT NULL OR objectives<>'[]'::jsonb OR common_errors<>'[]'::jsonb)
 OR EXISTS(SELECT 1 FROM lesson_versions WHERE review_round>0 OR (status='archived' AND published_at IS NULL)) OR EXISTS(SELECT 1 FROM lessons WHERE kind<>'lesson')
 OR EXISTS(SELECT 1 FROM mastery_records WHERE evaluation_level<>'non_evalué') THEN
  RAISE EXCEPTION 'Module 3 data present: downgrade would lose data' USING ERRCODE='23514';
 END IF;
END $$;
DROP TRIGGER t10_version_guard ON lesson_versions;
DROP TRIGGER t05_immutable ON lessons;
DROP TRIGGER t05_immutable ON content_reviews;
DROP TRIGGER t05_immutable ON lesson_competencies;
DROP TRIGGER t05_immutable ON lesson_sources;
DROP FUNCTION edu_guard_lesson_version();
DROP FUNCTION edu_immutable_content_record();
DROP INDEX uq_lesson_one_approved;
ALTER TABLE lesson_versions DROP CONSTRAINT ck_lesson_versions_status_values, DROP CONSTRAINT ck_lesson_versions_publication_date;
UPDATE lesson_versions SET status=CASE status WHEN 'pending_review' THEN 'in_review' WHEN 'approved' THEN 'published' WHEN 'archived' THEN 'retired' ELSE status END;
ALTER TABLE lesson_versions ADD CONSTRAINT ck_lesson_versions_status_values CHECK(status IN ('draft','in_review','published','retired')),
 ADD CONSTRAINT ck_lesson_versions_publication_date CHECK((status IN ('published','retired'))=(published_at IS NOT NULL));
ALTER TABLE lesson_versions DROP COLUMN editor_id,DROP COLUMN review_round;
ALTER TABLE lessons DROP COLUMN kind;
ALTER TABLE content_reviews DROP COLUMN review_round;
ALTER TABLE mastery_records DROP COLUMN evaluation_level;
ALTER TABLE competencies DROP COLUMN domain_id,DROP COLUMN objectives,DROP COLUMN common_errors;
DROP TABLE curriculum_domains;
ALTER TABLE lessons ENABLE ROW LEVEL SECURITY;
ALTER TABLE lesson_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE mastery_records ENABLE ROW LEVEL SECURITY;
REVOKE INSERT ON content_reviews,content_sources FROM edu_content;
REVOKE SELECT ON schools,user_roles FROM edu_curriculum,edu_content;
REVOKE SELECT(id,tenant_id,status,auth_version,deleted_at) ON users FROM edu_curriculum;
REVOKE SELECT ON students,guardians,guardian_students,teachers,teacher_classes,enrollments,mastery_records FROM edu_curriculum;
