ALTER TABLE ai_interactions ALTER COLUMN cost_eur DROP NOT NULL;
ALTER TABLE rag_documents ADD COLUMN page_selection jsonb NOT NULL DEFAULT '[]'::jsonb;
CREATE FUNCTION edu_rag_snapshot() RETURNS trigger LANGUAGE plpgsql AS $fn$
BEGIN
 IF TG_OP='UPDATE' AND (to_jsonb(NEW)-ARRAY['status','approved_by','approved_at','updated_at']) IS DISTINCT FROM
  (to_jsonb(OLD)-ARRAY['status','approved_by','approved_at','updated_at']) THEN
  RAISE EXCEPTION 'Document snapshot immutable' USING ERRCODE='23514';
 END IF;
 IF TG_OP='INSERT' AND NEW.status<>'draft' THEN
  RAISE EXCEPTION 'Draft required' USING ERRCODE='23514';
 END IF;
 IF TG_OP='UPDATE' AND NEW.status IS DISTINCT FROM OLD.status AND NOT
  ((OLD.status='draft' AND NEW.status='pending_review') OR
   (OLD.status='pending_review' AND NEW.status IN ('approved','draft')) OR
   (OLD.status='approved' AND NEW.status='archived')) THEN
  RAISE EXCEPTION 'Invalid transition' USING ERRCODE='23514';
 END IF;
 IF TG_OP='UPDATE' AND (NEW.approved_by IS DISTINCT FROM OLD.approved_by OR NEW.approved_at IS DISTINCT FROM OLD.approved_at)
  AND NOT (OLD.status='pending_review' AND NEW.status='approved') THEN
  RAISE EXCEPTION 'Approval immutable' USING ERRCODE='23514';
 END IF;
 IF NEW.status='approved' AND NOT EXISTS(SELECT 1 FROM rag_reviews r JOIN users u ON u.id=r.reviewer_id AND u.tenant_id=r.tenant_id
  JOIN user_roles ur ON ur.user_id=u.id AND ur.tenant_id=u.tenant_id WHERE r.document_id=NEW.id AND r.tenant_id=NEW.tenant_id
  AND r.decision='approved' AND r.reviewer_id=NEW.approved_by AND r.reviewer_id<>NEW.created_by
  AND u.status='active' AND ur.role IN ('teacher','content_creator')) THEN
  RAISE EXCEPTION 'Independent human review required' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $fn$;
CREATE TRIGGER t05_snapshot BEFORE INSERT OR UPDATE ON rag_documents FOR EACH ROW EXECUTE FUNCTION edu_rag_snapshot();
CREATE FUNCTION edu_rag_review() RETURNS trigger LANGUAGE plpgsql AS $fn$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM rag_documents d WHERE d.id=NEW.document_id AND d.tenant_id=NEW.tenant_id
  AND d.status='pending_review' AND d.created_by<>NEW.reviewer_id) OR NOT EXISTS(
  SELECT 1 FROM users u JOIN user_roles r ON r.user_id=u.id AND r.tenant_id=u.tenant_id
  WHERE u.id=NEW.reviewer_id AND u.tenant_id=NEW.tenant_id AND u.status='active' AND r.role IN ('teacher','content_creator')) THEN
  RAISE EXCEPTION 'Independent reviewer required' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $fn$;
CREATE TRIGGER t05_review BEFORE INSERT ON rag_reviews FOR EACH ROW EXECUTE FUNCTION edu_rag_review();
CREATE TRIGGER t05_immutable BEFORE UPDATE OR DELETE ON rag_reviews FOR EACH ROW EXECUTE FUNCTION edu_immutable_content_record();
CREATE TRIGGER t05_immutable BEFORE UPDATE OR DELETE ON rag_passages FOR EACH ROW EXECUTE FUNCTION edu_immutable_content_record();
CREATE FUNCTION edu_rag_passage() RETURNS trigger LANGUAGE plpgsql AS $fn$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM rag_documents WHERE id=NEW.document_id AND tenant_id=NEW.tenant_id AND status='draft') THEN
  RAISE EXCEPTION 'Draft document required' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $fn$;
CREATE TRIGGER t04_passage BEFORE INSERT ON rag_passages FOR EACH ROW EXECUTE FUNCTION edu_rag_passage();
CREATE TRIGGER t05_immutable BEFORE UPDATE ON tutor_turns FOR EACH ROW EXECUTE FUNCTION edu_immutable_content_record();
GRANT SELECT ON schools,user_roles TO edu_ai_router,edu_retrieval,edu_tutor;
GRANT SELECT(id,tenant_id,status,auth_version,deleted_at) ON users TO edu_ai_router,edu_retrieval,edu_tutor;
GRANT SELECT ON students,exercise_attempts,learning_sessions,exercise_competencies TO edu_ai_router,edu_tutor;
GRANT SELECT ON rag_documents,rag_passages TO edu_ai_router,edu_tutor;
GRANT SELECT,INSERT ON rag_documents,rag_passages,rag_reviews TO edu_retrieval;
GRANT UPDATE(status,approved_by,approved_at) ON rag_documents TO edu_retrieval;
GRANT SELECT,INSERT,DELETE ON tutor_turns TO edu_tutor;
GRANT UPDATE(max_hint_level) ON exercise_attempts TO edu_tutor;
REVOKE ALL ON FUNCTION edu_rag_snapshot(),edu_rag_review(),edu_rag_passage() FROM PUBLIC;
