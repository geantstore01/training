
CREATE TABLE rag_documents (
	url TEXT NOT NULL, 
	title VARCHAR(240) NOT NULL, 
	checksum VARCHAR(64) NOT NULL, 
	version INTEGER NOT NULL, 
	level VARCHAR(3) NOT NULL, 
	subject VARCHAR(30) NOT NULL, 
	programme_version VARCHAR(80) NOT NULL, 
	effective_from DATE NOT NULL, 
	effective_until DATE, 
	status VARCHAR(20) DEFAULT 'draft' NOT NULL, 
	created_by UUID NOT NULL, 
	approved_by UUID, 
	approved_at TIMESTAMP WITH TIME ZONE, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_rag_documents PRIMARY KEY (id), 
	CONSTRAINT fk_rag_documents_tenant_id_users FOREIGN KEY(tenant_id, created_by) REFERENCES users (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT fk_rag_approved_user FOREIGN KEY(tenant_id, approved_by) REFERENCES users (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_rag_document_version UNIQUE (tenant_id, url, level, subject, version), 
	CONSTRAINT ck_rag_documents_status_values CHECK (status IN ('draft','pending_review','approved','archived')), 
	CONSTRAINT ck_rag_documents_level_values CHECK (level IN ('CM1','CM2')), 
	CONSTRAINT ck_rag_documents_subject_values CHECK (subject IN ('francais','mathematiques','histoire')), 
	CONSTRAINT ck_rag_documents_snapshot CHECK (version > 0 AND checksum ~ '^[a-f0-9]{64}$'), 
	CONSTRAINT ck_rag_documents_dates CHECK (effective_until IS NULL OR effective_until >= effective_from), 
	CONSTRAINT ck_rag_documents_approval CHECK ((approved_by IS NULL) = (approved_at IS NULL) AND (status <> 'approved' OR approved_by IS NOT NULL)), 
	CONSTRAINT uq_rag_documents_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_rag_documents_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;
CREATE INDEX ix_rag_documents_tenant_id ON rag_documents (tenant_id);
ALTER TABLE rag_documents ENABLE ROW LEVEL SECURITY; ALTER TABLE rag_documents FORCE ROW LEVEL SECURITY; CREATE POLICY tenant_isolation ON rag_documents USING(tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid) WITH CHECK(tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid); CREATE TRIGGER t90_updated_at BEFORE UPDATE ON rag_documents FOR EACH ROW EXECUTE FUNCTION edu_touch_updated_at();

CREATE TABLE rag_passages (
	document_id UUID NOT NULL, 
	ordinal INTEGER NOT NULL, 
	body TEXT NOT NULL, 
	embedding VECTOR(768) NOT NULL, 
	embedding_model VARCHAR(100) NOT NULL, 
	search_vector TSVECTOR GENERATED ALWAYS AS (to_tsvector('french', body)) STORED NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_rag_passages PRIMARY KEY (id), 
	CONSTRAINT fk_rag_passages_tenant_id_rag_documents FOREIGN KEY(tenant_id, document_id) REFERENCES rag_documents (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_rag_passages_tenant_id_document_id_ordinal UNIQUE (tenant_id, document_id, ordinal), 
	CONSTRAINT ck_rag_passages_bounds CHECK (ordinal >= 0 AND length(body) BETWEEN 1 AND 1800), 
	CONSTRAINT uq_rag_passages_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_rag_passages_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;
CREATE INDEX ix_rag_passages_tenant_id ON rag_passages (tenant_id);
CREATE INDEX ix_rag_search ON rag_passages USING gin (search_vector);
CREATE INDEX ix_rag_vector ON rag_passages USING hnsw (embedding vector_cosine_ops);
ALTER TABLE rag_passages ENABLE ROW LEVEL SECURITY; ALTER TABLE rag_passages FORCE ROW LEVEL SECURITY; CREATE POLICY tenant_isolation ON rag_passages USING(tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid) WITH CHECK(tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid); CREATE TRIGGER t90_updated_at BEFORE UPDATE ON rag_passages FOR EACH ROW EXECUTE FUNCTION edu_touch_updated_at();

CREATE TABLE rag_reviews (
	document_id UUID NOT NULL, 
	reviewer_id UUID NOT NULL, 
	decision VARCHAR(20) NOT NULL, 
	reason_code VARCHAR(50) NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_rag_reviews PRIMARY KEY (id), 
	CONSTRAINT fk_rag_reviews_tenant_id_rag_documents FOREIGN KEY(tenant_id, document_id) REFERENCES rag_documents (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT fk_rag_reviews_tenant_id_users FOREIGN KEY(tenant_id, reviewer_id) REFERENCES users (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT ck_rag_reviews_decision_values CHECK (decision IN ('approved','rejected')), 
	CONSTRAINT uq_rag_reviews_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_rag_reviews_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;
CREATE INDEX ix_rag_reviews_tenant_id ON rag_reviews (tenant_id);
ALTER TABLE rag_reviews ENABLE ROW LEVEL SECURITY; ALTER TABLE rag_reviews FORCE ROW LEVEL SECURITY; CREATE POLICY tenant_isolation ON rag_reviews USING(tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid) WITH CHECK(tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid); CREATE TRIGGER t90_updated_at BEFORE UPDATE ON rag_reviews FOR EACH ROW EXECUTE FUNCTION edu_touch_updated_at();

CREATE TABLE tutor_turns (
	attempt_id UUID NOT NULL, 
	request_id UUID NOT NULL, 
	request_digest VARCHAR(64) NOT NULL, 
	level INTEGER NOT NULL, 
	response JSONB NOT NULL, 
	passage_ids JSONB NOT NULL, 
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_tutor_turns PRIMARY KEY (id), 
	CONSTRAINT fk_tutor_turns_tenant_id_exercise_attempts FOREIGN KEY(tenant_id, attempt_id) REFERENCES exercise_attempts (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_tutor_turns_tenant_id_attempt_id_request_id UNIQUE (tenant_id, attempt_id, request_id), 
	CONSTRAINT ck_tutor_turns_level CHECK (level BETWEEN 0 AND 6), 
	CONSTRAINT uq_tutor_turns_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_tutor_turns_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;
CREATE INDEX ix_tutor_history ON tutor_turns (tenant_id, attempt_id, created_at);
CREATE INDEX ix_tutor_turns_tenant_id ON tutor_turns (tenant_id);
ALTER TABLE tutor_turns ENABLE ROW LEVEL SECURITY; ALTER TABLE tutor_turns FORCE ROW LEVEL SECURITY; CREATE POLICY tenant_isolation ON tutor_turns USING(tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid) WITH CHECK(tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid); CREATE TRIGGER t90_updated_at BEFORE UPDATE ON tutor_turns FOR EACH ROW EXECUTE FUNCTION edu_touch_updated_at();
