
CREATE TABLE tutor_controls (
	student_id UUID NOT NULL, 
	enabled BOOLEAN DEFAULT true NOT NULL, 
	max_help INTEGER DEFAULT 6 NOT NULL, 
	changed_by UUID NOT NULL, 
	revision INTEGER DEFAULT 1 NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_tutor_controls PRIMARY KEY (id), 
	CONSTRAINT fk_tutor_controls_tenant_id_students FOREIGN KEY(tenant_id, student_id) REFERENCES students (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT fk_tutor_controls_tenant_id_users FOREIGN KEY(tenant_id, changed_by) REFERENCES users (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_tutor_controls_tenant_id_student_id UNIQUE (tenant_id, student_id), 
	CONSTRAINT ck_tutor_controls_help_range CHECK (max_help BETWEEN 0 AND 6), 
	CONSTRAINT ck_tutor_controls_control_revision CHECK (revision >= 1), 
	CONSTRAINT uq_tutor_controls_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_tutor_controls_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;
CREATE INDEX ix_tutor_controls_tenant_id ON tutor_controls (tenant_id);
ALTER TABLE tutor_controls ENABLE ROW LEVEL SECURITY;
ALTER TABLE tutor_controls FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON tutor_controls USING(tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid) WITH CHECK(tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid);
CREATE TRIGGER t90_updated_at BEFORE UPDATE ON tutor_controls FOR EACH ROW EXECUTE FUNCTION edu_touch_updated_at();
GRANT SELECT,INSERT,UPDATE ON tutor_controls TO edu_class;
GRANT SELECT ON tutor_controls TO edu_tutor,edu_ai_router,edu_assessment;
