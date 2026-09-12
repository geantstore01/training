
CREATE TABLE missions (
	class_id UUID NOT NULL, 
	group_id UUID, 
	author_id UUID NOT NULL, 
	title VARCHAR(160) NOT NULL, 
	day DATE NOT NULL, 
	status VARCHAR(20) DEFAULT 'published' NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_missions PRIMARY KEY (id), 
	CONSTRAINT fk_missions_tenant_id_classes FOREIGN KEY(tenant_id, class_id) REFERENCES classes (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT fk_missions_tenant_id_learning_groups FOREIGN KEY(tenant_id, group_id) REFERENCES learning_groups (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT fk_missions_tenant_id_users FOREIGN KEY(tenant_id, author_id) REFERENCES users (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT ck_missions_status_values CHECK (status IN ('published','archived')), 
	CONSTRAINT uq_missions_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_missions_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;
CREATE INDEX ix_missions_tenant_id ON missions (tenant_id);
ALTER TABLE missions ENABLE ROW LEVEL SECURITY; ALTER TABLE missions FORCE ROW LEVEL SECURITY; CREATE POLICY tenant_isolation ON missions USING(tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid) WITH CHECK(tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid);
CREATE TRIGGER t90_updated_at BEFORE UPDATE ON missions FOR EACH ROW EXECUTE FUNCTION edu_touch_updated_at();

CREATE TABLE mission_exercises (
	mission_id UUID NOT NULL, 
	exercise_version_id UUID NOT NULL, 
	ordinal INTEGER NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_mission_exercises PRIMARY KEY (id), 
	CONSTRAINT fk_mission_exercises_tenant_id_missions FOREIGN KEY(tenant_id, mission_id) REFERENCES missions (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT fk_mission_exercises_tenant_id_exercise_versions FOREIGN KEY(tenant_id, exercise_version_id) REFERENCES exercise_versions (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_mission_exercises_tenant_id_mission_id_exercise_version_id UNIQUE (tenant_id, mission_id, exercise_version_id), 
	CONSTRAINT ck_mission_exercises_ordinal CHECK (ordinal >= 0), 
	CONSTRAINT uq_mission_exercises_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_mission_exercises_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;
CREATE INDEX ix_mission_exercises_tenant_id ON mission_exercises (tenant_id);
ALTER TABLE mission_exercises ENABLE ROW LEVEL SECURITY; ALTER TABLE mission_exercises FORCE ROW LEVEL SECURITY; CREATE POLICY tenant_isolation ON mission_exercises USING(tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid) WITH CHECK(tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid);
CREATE TRIGGER t90_updated_at BEFORE UPDATE ON mission_exercises FOR EACH ROW EXECUTE FUNCTION edu_touch_updated_at();

CREATE TABLE feature_flags (
	key VARCHAR(40) NOT NULL, 
	enabled BOOLEAN NOT NULL, 
	changed_by UUID NOT NULL, 
	revision INTEGER DEFAULT '1' NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_feature_flags PRIMARY KEY (id), 
	CONSTRAINT fk_feature_flags_tenant_id_users FOREIGN KEY(tenant_id, changed_by) REFERENCES users (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_feature_flags_tenant_id_key UNIQUE (tenant_id, key), 
	CONSTRAINT ck_feature_flags_key_values CHECK (key IN ('missions','speech','notifications')), 
	CONSTRAINT ck_feature_flags_revision CHECK (revision > 0), 
	CONSTRAINT uq_feature_flags_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_feature_flags_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;
CREATE INDEX ix_feature_flags_tenant_id ON feature_flags (tenant_id);
ALTER TABLE feature_flags ENABLE ROW LEVEL SECURITY; ALTER TABLE feature_flags FORCE ROW LEVEL SECURITY; CREATE POLICY tenant_isolation ON feature_flags USING(tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid) WITH CHECK(tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid);
CREATE TRIGGER t90_updated_at BEFORE UPDATE ON feature_flags FOR EACH ROW EXECUTE FUNCTION edu_touch_updated_at();

CREATE TABLE safety_cases (
	event_id UUID NOT NULL, 
	reviewer_id UUID NOT NULL, 
	resolution VARCHAR(40) NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_safety_cases PRIMARY KEY (id), 
	CONSTRAINT fk_safety_cases_tenant_id_safety_events FOREIGN KEY(tenant_id, event_id) REFERENCES safety_events (tenant_id, id) ON DELETE CASCADE, 
	CONSTRAINT fk_safety_cases_tenant_id_users FOREIGN KEY(tenant_id, reviewer_id) REFERENCES users (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_safety_cases_tenant_id_event_id UNIQUE (tenant_id, event_id), 
	CONSTRAINT ck_safety_cases_resolution_values CHECK (resolution IN ('reviewed','escalated','false_positive')), 
	CONSTRAINT uq_safety_cases_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_safety_cases_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;
CREATE INDEX ix_safety_cases_tenant_id ON safety_cases (tenant_id);
ALTER TABLE safety_cases ENABLE ROW LEVEL SECURITY; ALTER TABLE safety_cases FORCE ROW LEVEL SECURITY; CREATE POLICY tenant_isolation ON safety_cases USING(tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid) WITH CHECK(tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid);
CREATE TRIGGER t90_updated_at BEFORE UPDATE ON safety_cases FOR EACH ROW EXECUTE FUNCTION edu_touch_updated_at();

CREATE TABLE background_jobs (
	requested_by UUID NOT NULL, 
	kind VARCHAR(40) NOT NULL, 
	idempotency_key UUID NOT NULL, 
	payload JSONB NOT NULL, 
	status VARCHAR(20) DEFAULT 'queued' NOT NULL, 
	attempts INTEGER DEFAULT '0' NOT NULL, 
	available_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	error_code VARCHAR(80), 
	result JSONB, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_background_jobs PRIMARY KEY (id), 
	CONSTRAINT fk_background_jobs_tenant_id_users FOREIGN KEY(tenant_id, requested_by) REFERENCES users (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_background_jobs_tenant_id_idempotency_key UNIQUE (tenant_id, idempotency_key), 
	CONSTRAINT ck_background_jobs_kind_values CHECK (kind IN ('weekly_reports','difficulty_alerts','exercise_batch','privacy_purge')), 
	CONSTRAINT ck_background_jobs_status_values CHECK (status IN ('queued','completed','failed')), 
	CONSTRAINT ck_background_jobs_attempts CHECK (attempts BETWEEN 0 AND 5), 
	CONSTRAINT uq_background_jobs_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_background_jobs_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;
CREATE INDEX ix_background_jobs_tenant_id ON background_jobs (tenant_id);
CREATE INDEX ix_jobs_ready ON background_jobs (status, available_at);
ALTER TABLE background_jobs ENABLE ROW LEVEL SECURITY; ALTER TABLE background_jobs FORCE ROW LEVEL SECURITY; CREATE POLICY tenant_isolation ON background_jobs USING(tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid) WITH CHECK(tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid);
CREATE TRIGGER t90_updated_at BEFORE UPDATE ON background_jobs FOR EACH ROW EXECUTE FUNCTION edu_touch_updated_at();

CREATE TABLE notifications (
	recipient_id UUID NOT NULL, 
	student_id UUID NOT NULL, 
	kind VARCHAR(40) NOT NULL, 
	period DATE NOT NULL, 
	body JSONB NOT NULL, 
	read_at TIMESTAMP WITH TIME ZONE, 
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_notifications PRIMARY KEY (id), 
	CONSTRAINT fk_notifications_tenant_id_users FOREIGN KEY(tenant_id, recipient_id) REFERENCES users (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT fk_notifications_tenant_id_students FOREIGN KEY(tenant_id, student_id) REFERENCES students (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_notification_period UNIQUE (tenant_id, recipient_id, student_id, kind, period), 
	CONSTRAINT ck_notifications_kind_values CHECK (kind IN ('weekly_report','difficulty_alert')), 
	CONSTRAINT uq_notifications_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_notifications_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;
CREATE INDEX ix_notifications_tenant_id ON notifications (tenant_id);
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY; ALTER TABLE notifications FORCE ROW LEVEL SECURITY; CREATE POLICY tenant_isolation ON notifications USING(tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid) WITH CHECK(tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid);
CREATE TRIGGER t90_updated_at BEFORE UPDATE ON notifications FOR EACH ROW EXECUTE FUNCTION edu_touch_updated_at();

CREATE TABLE job_dispatch (
	school_id UUID NOT NULL, 
	job_id UUID NOT NULL, 
	ready_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_job_dispatch PRIMARY KEY (id), 
	CONSTRAINT fk_job_dispatch_school_id_tenants FOREIGN KEY(school_id) REFERENCES tenants (id) ON DELETE RESTRICT, 
	CONSTRAINT uq_job_dispatch_job_id UNIQUE (job_id), 
	CONSTRAINT fk_job_dispatch_school_id_background_jobs FOREIGN KEY(school_id, job_id) REFERENCES background_jobs (tenant_id, id) ON DELETE CASCADE
)

;
CREATE INDEX ix_job_dispatch_ready_at ON job_dispatch (ready_at);
CREATE TRIGGER t90_updated_at BEFORE UPDATE ON job_dispatch FOR EACH ROW EXECUTE FUNCTION edu_touch_updated_at();
