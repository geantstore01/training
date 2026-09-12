-- Révision 0001 figée. Extension vector et rôles installés par infra/postgres/init.sh.

CREATE TABLE curriculum_levels (
	code VARCHAR(3) NOT NULL, 
	cycle INTEGER DEFAULT '3' NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_curriculum_levels PRIMARY KEY (id), 
	CONSTRAINT ck_curriculum_levels_code_values CHECK (code IN ('CM1','CM2')), 
	CONSTRAINT ck_curriculum_levels_cycle_three CHECK (cycle = 3), 
	CONSTRAINT uq_curriculum_levels_code UNIQUE (code)
);

CREATE TABLE subjects (
	code VARCHAR(40) NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_subjects PRIMARY KEY (id), 
	CONSTRAINT uq_subjects_code UNIQUE (code)
);

CREATE TABLE tenants (
	name VARCHAR(200) NOT NULL, 
	status VARCHAR(20) DEFAULT 'active' NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_tenants PRIMARY KEY (id), 
	CONSTRAINT ck_tenants_status_values CHECK (status IN ('active','suspended','closing'))
);

CREATE TABLE competencies (
	subject_id UUID NOT NULL, 
	curriculum_level_id UUID NOT NULL, 
	code VARCHAR(80) NOT NULL, 
	label TEXT NOT NULL, 
	description TEXT NOT NULL, 
	official_reference_url TEXT NOT NULL, 
	programme_version VARCHAR(80) NOT NULL, 
	effective_from DATE NOT NULL, 
	effective_until DATE, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_competencies PRIMARY KEY (id), 
	CONSTRAINT uq_competencies_code_programme_version UNIQUE (code, programme_version), 
	CONSTRAINT ck_competencies_validity_order CHECK (effective_until IS NULL OR effective_until >= effective_from), 
	CONSTRAINT fk_competencies_subject_id_subjects FOREIGN KEY(subject_id) REFERENCES subjects (id), 
	CONSTRAINT fk_competencies_curriculum_level_id_curriculum_levels FOREIGN KEY(curriculum_level_id) REFERENCES curriculum_levels (id)
);

CREATE INDEX ix_competencies_curriculum_level_id ON competencies (curriculum_level_id);

CREATE INDEX ix_competencies_subject_id ON competencies (subject_id);

CREATE TABLE schools (
	name VARCHAR(200) NOT NULL, 
	uai VARCHAR(8), 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_schools PRIMARY KEY (id), 
	CONSTRAINT uq_schools_tenant_id_uai UNIQUE (tenant_id, uai), 
	CONSTRAINT uq_schools_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_schools_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_schools_tenant_id ON schools (tenant_id);

CREATE TABLE users (
	login VARCHAR(254) NOT NULL, 
	email_ciphertext BYTEA, 
	password_hash TEXT, 
	status VARCHAR(20) DEFAULT 'pending' NOT NULL, 
	last_login_at TIMESTAMP WITH TIME ZONE, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_users PRIMARY KEY (id), 
	CONSTRAINT uq_users_tenant_id_login UNIQUE (tenant_id, login), 
	CONSTRAINT ck_users_status_values CHECK (status IN ('pending','active','locked','deleted')), 
	CONSTRAINT ck_users_normalized_login CHECK (login = lower(login) AND length(login) >= 3), 
	CONSTRAINT uq_users_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_users_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_users_tenant_id ON users (tenant_id);

CREATE TABLE audit_logs (
	actor_id UUID, 
	action VARCHAR(120) NOT NULL, 
	resource_type VARCHAR(80) NOT NULL, 
	resource_id UUID, 
	correlation_id UUID NOT NULL, 
	outcome VARCHAR(20) NOT NULL, 
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_audit_logs PRIMARY KEY (id), 
	CONSTRAINT fk_audit_logs_tenant_id_users FOREIGN KEY(tenant_id, actor_id) REFERENCES users (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT ck_audit_logs_outcome_values CHECK (outcome IN ('success','denied','failure')), 
	CONSTRAINT ck_audit_logs_retention_order CHECK (expires_at > created_at), 
	CONSTRAINT uq_audit_logs_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_audit_logs_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_audit_logs_expires_at ON audit_logs (expires_at);

CREATE INDEX ix_audit_logs_tenant_id ON audit_logs (tenant_id);

CREATE INDEX ix_audit_time ON audit_logs (tenant_id, created_at);

CREATE TABLE classes (
	school_id UUID NOT NULL, 
	name VARCHAR(80) NOT NULL, 
	academic_year INTEGER NOT NULL, 
	curriculum_level_id UUID, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_classes PRIMARY KEY (id), 
	CONSTRAINT fk_classes_tenant_id_schools FOREIGN KEY(tenant_id, school_id) REFERENCES schools (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_classes_tenant_id_school_id_name_academic_year UNIQUE (tenant_id, school_id, name, academic_year), 
	CONSTRAINT ck_classes_year_range CHECK (academic_year BETWEEN 2020 AND 2200), 
	CONSTRAINT uq_classes_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_classes_curriculum_level_id_curriculum_levels FOREIGN KEY(curriculum_level_id) REFERENCES curriculum_levels (id), 
	CONSTRAINT fk_classes_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_classes_tenant_id ON classes (tenant_id);

CREATE TABLE competency_prerequisites (
	competency_id UUID NOT NULL, 
	prerequisite_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_competency_prerequisites PRIMARY KEY (id), 
	CONSTRAINT uq_competency_prerequisites_competency_id_prerequisite_id UNIQUE (competency_id, prerequisite_id), 
	CONSTRAINT ck_competency_prerequisites_no_self_dependency CHECK (competency_id <> prerequisite_id), 
	CONSTRAINT fk_competency_prerequisites_competency_id_competencies FOREIGN KEY(competency_id) REFERENCES competencies (id), 
	CONSTRAINT fk_competency_prerequisites_prerequisite_id_competencies FOREIGN KEY(prerequisite_id) REFERENCES competencies (id)
);

CREATE TABLE content_sources (
	title VARCHAR(240) NOT NULL, 
	url TEXT NOT NULL, 
	publisher VARCHAR(200) NOT NULL, 
	license TEXT NOT NULL, 
	checksum_sha256 VARCHAR(64) NOT NULL, 
	retrieved_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	approved_by UUID, 
	approved_at TIMESTAMP WITH TIME ZONE, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_content_sources PRIMARY KEY (id), 
	CONSTRAINT fk_content_sources_tenant_id_users FOREIGN KEY(tenant_id, approved_by) REFERENCES users (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_content_sources_tenant_id_checksum_sha256 UNIQUE (tenant_id, checksum_sha256), 
	CONSTRAINT ck_content_sources_sha256_format CHECK (checksum_sha256 ~ '^[a-f0-9]{64}$'), 
	CONSTRAINT ck_content_sources_approval_pair CHECK ((approved_by IS NULL) = (approved_at IS NULL)), 
	CONSTRAINT uq_content_sources_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_content_sources_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_content_sources_tenant_id ON content_sources (tenant_id);

CREATE TABLE exercises (
	slug VARCHAR(160) NOT NULL, 
	author_id UUID NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_exercises PRIMARY KEY (id), 
	CONSTRAINT fk_exercises_tenant_id_users FOREIGN KEY(tenant_id, author_id) REFERENCES users (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_exercises_tenant_id_slug UNIQUE (tenant_id, slug), 
	CONSTRAINT uq_exercises_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_exercises_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_exercises_tenant_id ON exercises (tenant_id);

CREATE TABLE guardians (
	user_id UUID NOT NULL, 
	identity_ciphertext BYTEA, 
	verified_at TIMESTAMP WITH TIME ZONE, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_guardians PRIMARY KEY (id), 
	CONSTRAINT fk_guardians_tenant_id_users FOREIGN KEY(tenant_id, user_id) REFERENCES users (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_guardians_tenant_id_user_id UNIQUE (tenant_id, user_id), 
	CONSTRAINT uq_guardians_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_guardians_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_guardians_tenant_id ON guardians (tenant_id);

CREATE TABLE lessons (
	slug VARCHAR(160) NOT NULL, 
	author_id UUID NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_lessons PRIMARY KEY (id), 
	CONSTRAINT fk_lessons_tenant_id_users FOREIGN KEY(tenant_id, author_id) REFERENCES users (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_lessons_tenant_id_slug UNIQUE (tenant_id, slug), 
	CONSTRAINT uq_lessons_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_lessons_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_lessons_tenant_id ON lessons (tenant_id);

CREATE TABLE students (
	user_id UUID NOT NULL, 
	pseudonym VARCHAR(80) NOT NULL, 
	curriculum_level_id UUID NOT NULL, 
	accessibility_preferences JSONB DEFAULT '{}'::jsonb NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_students PRIMARY KEY (id), 
	CONSTRAINT fk_students_tenant_id_users FOREIGN KEY(tenant_id, user_id) REFERENCES users (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_students_tenant_id_user_id UNIQUE (tenant_id, user_id), 
	CONSTRAINT ck_students_preferences_object CHECK (jsonb_typeof(accessibility_preferences) = 'object'), 
	CONSTRAINT uq_students_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_students_curriculum_level_id_curriculum_levels FOREIGN KEY(curriculum_level_id) REFERENCES curriculum_levels (id), 
	CONSTRAINT fk_students_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_students_tenant_id ON students (tenant_id);

CREATE TABLE teachers (
	user_id UUID NOT NULL, 
	display_name VARCHAR(120) NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_teachers PRIMARY KEY (id), 
	CONSTRAINT fk_teachers_tenant_id_users FOREIGN KEY(tenant_id, user_id) REFERENCES users (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_teachers_tenant_id_user_id UNIQUE (tenant_id, user_id), 
	CONSTRAINT uq_teachers_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_teachers_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_teachers_tenant_id ON teachers (tenant_id);

CREATE TABLE user_roles (
	user_id UUID NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_user_roles PRIMARY KEY (id), 
	CONSTRAINT fk_user_roles_tenant_id_users FOREIGN KEY(tenant_id, user_id) REFERENCES users (tenant_id, id) ON DELETE CASCADE, 
	CONSTRAINT uq_user_roles_tenant_id_user_id_role UNIQUE (tenant_id, user_id, role), 
	CONSTRAINT ck_user_roles_role_values CHECK (role IN ('student','guardian','teacher','school_admin','moderator','tenant_admin')), 
	CONSTRAINT uq_user_roles_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_user_roles_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_user_roles_tenant_id ON user_roles (tenant_id);

CREATE TABLE content_chunks (
	source_id UUID NOT NULL, 
	ordinal INTEGER NOT NULL, 
	body TEXT NOT NULL, 
	embedding VECTOR(768), 
	embedding_model VARCHAR(120), 
	search_vector TSVECTOR GENERATED ALWAYS AS (to_tsvector('french'::regconfig, body)) STORED NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_content_chunks PRIMARY KEY (id), 
	CONSTRAINT fk_content_chunks_tenant_id_content_sources FOREIGN KEY(tenant_id, source_id) REFERENCES content_sources (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_content_chunks_tenant_id_source_id_ordinal UNIQUE (tenant_id, source_id, ordinal), 
	CONSTRAINT ck_content_chunks_ordinal_range CHECK (ordinal >= 0), 
	CONSTRAINT ck_content_chunks_embedding_pair CHECK ((embedding IS NULL) = (embedding_model IS NULL)), 
	CONSTRAINT uq_content_chunks_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_content_chunks_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_chunks_fts ON content_chunks USING gin (search_vector);

CREATE INDEX ix_chunks_vector ON content_chunks USING hnsw (embedding vector_cosine_ops);

CREATE INDEX ix_content_chunks_tenant_id ON content_chunks (tenant_id);

CREATE TABLE enrollments (
	student_id UUID NOT NULL, 
	class_id UUID NOT NULL, 
	starts_on DATE NOT NULL, 
	ends_on DATE, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_enrollments PRIMARY KEY (id), 
	CONSTRAINT fk_enrollments_tenant_id_students FOREIGN KEY(tenant_id, student_id) REFERENCES students (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT fk_enrollments_tenant_id_classes FOREIGN KEY(tenant_id, class_id) REFERENCES classes (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_enrollments_tenant_id_student_id_class_id_starts_on UNIQUE (tenant_id, student_id, class_id, starts_on), 
	CONSTRAINT ck_enrollments_date_order CHECK (ends_on IS NULL OR ends_on >= starts_on), 
	CONSTRAINT uq_enrollments_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_enrollments_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_enrollments_tenant_id ON enrollments (tenant_id);

CREATE UNIQUE INDEX uq_enrollments_active ON enrollments (tenant_id, student_id, class_id) WHERE ends_on IS NULL;

CREATE TABLE exercise_versions (
	exercise_id UUID NOT NULL, 
	version INTEGER NOT NULL, 
	kind VARCHAR(30) NOT NULL, 
	prompt JSONB NOT NULL, 
	answer_spec JSONB NOT NULL, 
	validator_name VARCHAR(120) NOT NULL, 
	validator_version VARCHAR(40) NOT NULL, 
	difficulty INTEGER NOT NULL, 
	status VARCHAR(20) DEFAULT 'draft' NOT NULL, 
	published_at TIMESTAMP WITH TIME ZONE, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_exercise_versions PRIMARY KEY (id), 
	CONSTRAINT fk_exercise_versions_tenant_id_exercises FOREIGN KEY(tenant_id, exercise_id) REFERENCES exercises (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_exercise_versions_tenant_id_exercise_id_version UNIQUE (tenant_id, exercise_id, version), 
	CONSTRAINT ck_exercise_versions_version_difficulty CHECK (version > 0 AND difficulty BETWEEN 1 AND 5), 
	CONSTRAINT ck_exercise_versions_kind_values CHECK (kind IN ('multiple_choice','integer','decimal','fraction','short_text','ordering','matching')), 
	CONSTRAINT ck_exercise_versions_status_values CHECK (status IN ('draft','in_review','published','retired')), 
	CONSTRAINT ck_exercise_versions_publication_date CHECK ((status IN ('published','retired')) = (published_at IS NOT NULL)), 
	CONSTRAINT uq_exercise_versions_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_exercise_versions_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_exercise_versions_tenant_id ON exercise_versions (tenant_id);

CREATE TABLE guardian_students (
	guardian_id UUID NOT NULL, 
	student_id UUID NOT NULL, 
	relationship VARCHAR(20) NOT NULL, 
	authority_verified_at TIMESTAMP WITH TIME ZONE, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_guardian_students PRIMARY KEY (id), 
	CONSTRAINT fk_guardian_students_tenant_id_guardians FOREIGN KEY(tenant_id, guardian_id) REFERENCES guardians (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT fk_guardian_students_tenant_id_students FOREIGN KEY(tenant_id, student_id) REFERENCES students (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_guardian_students_tenant_id_guardian_id_student_id UNIQUE (tenant_id, guardian_id, student_id), 
	CONSTRAINT ck_guardian_students_relationship_values CHECK (relationship IN ('parent','legal_guardian')), 
	CONSTRAINT uq_guardian_students_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_guardian_students_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_guardian_students_tenant_id ON guardian_students (tenant_id);

CREATE TABLE learning_groups (
	class_id UUID NOT NULL, 
	name VARCHAR(80) NOT NULL, 
	competency_id UUID, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_learning_groups PRIMARY KEY (id), 
	CONSTRAINT fk_learning_groups_tenant_id_classes FOREIGN KEY(tenant_id, class_id) REFERENCES classes (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_learning_groups_tenant_id_class_id_name UNIQUE (tenant_id, class_id, name), 
	CONSTRAINT uq_learning_groups_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_learning_groups_competency_id_competencies FOREIGN KEY(competency_id) REFERENCES competencies (id), 
	CONSTRAINT fk_learning_groups_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_learning_groups_tenant_id ON learning_groups (tenant_id);

CREATE TABLE learning_sessions (
	student_id UUID NOT NULL, 
	started_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	ended_at TIMESTAMP WITH TIME ZONE, 
	status VARCHAR(20) DEFAULT 'active' NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_learning_sessions PRIMARY KEY (id), 
	CONSTRAINT fk_learning_sessions_tenant_id_students FOREIGN KEY(tenant_id, student_id) REFERENCES students (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_learning_sessions_tenant_id_id_student_id UNIQUE (tenant_id, id, student_id), 
	CONSTRAINT ck_learning_sessions_status_values CHECK (status IN ('active','completed','abandoned')), 
	CONSTRAINT ck_learning_sessions_time_order CHECK (ended_at IS NULL OR ended_at >= started_at), 
	CONSTRAINT ck_learning_sessions_session_end CHECK ((status = 'active') = (ended_at IS NULL)), 
	CONSTRAINT uq_learning_sessions_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_learning_sessions_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_learning_sessions_tenant_id ON learning_sessions (tenant_id);

CREATE TABLE lesson_versions (
	lesson_id UUID NOT NULL, 
	version INTEGER NOT NULL, 
	title VARCHAR(240) NOT NULL, 
	body JSONB NOT NULL, 
	status VARCHAR(20) DEFAULT 'draft' NOT NULL, 
	published_at TIMESTAMP WITH TIME ZONE, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_lesson_versions PRIMARY KEY (id), 
	CONSTRAINT fk_lesson_versions_tenant_id_lessons FOREIGN KEY(tenant_id, lesson_id) REFERENCES lessons (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_lesson_versions_tenant_id_lesson_id_version UNIQUE (tenant_id, lesson_id, version), 
	CONSTRAINT ck_lesson_versions_positive_version CHECK (version > 0), 
	CONSTRAINT ck_lesson_versions_status_values CHECK (status IN ('draft','in_review','published','retired')), 
	CONSTRAINT ck_lesson_versions_publication_date CHECK ((status IN ('published','retired')) = (published_at IS NOT NULL)), 
	CONSTRAINT uq_lesson_versions_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_lesson_versions_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_lesson_versions_tenant_id ON lesson_versions (tenant_id);

CREATE TABLE mastery_records (
	student_id UUID NOT NULL, 
	competency_id UUID NOT NULL, 
	probability NUMERIC(6, 5) NOT NULL, 
	evidence_count INTEGER DEFAULT '0' NOT NULL, 
	algorithm_version VARCHAR(40) NOT NULL, 
	last_assessed_at TIMESTAMP WITH TIME ZONE, 
	revision INTEGER DEFAULT '1' NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_mastery_records PRIMARY KEY (id), 
	CONSTRAINT fk_mastery_records_tenant_id_students FOREIGN KEY(tenant_id, student_id) REFERENCES students (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_mastery_records_tenant_id_student_id_competency_id UNIQUE (tenant_id, student_id, competency_id), 
	CONSTRAINT ck_mastery_records_mastery_range CHECK (probability BETWEEN 0 AND 1 AND evidence_count >= 0 AND revision > 0), 
	CONSTRAINT uq_mastery_records_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_mastery_records_competency_id_competencies FOREIGN KEY(competency_id) REFERENCES competencies (id), 
	CONSTRAINT fk_mastery_records_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_mastery_records_tenant_id ON mastery_records (tenant_id);

CREATE TABLE spaced_repetition_items (
	student_id UUID NOT NULL, 
	competency_id UUID NOT NULL, 
	due_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	interval_days INTEGER DEFAULT '0' NOT NULL, 
	ease_factor NUMERIC(5, 3) DEFAULT '2.5' NOT NULL, 
	repetitions INTEGER DEFAULT '0' NOT NULL, 
	algorithm_version VARCHAR(40) NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_spaced_repetition_items PRIMARY KEY (id), 
	CONSTRAINT fk_spaced_repetition_items_tenant_id_students FOREIGN KEY(tenant_id, student_id) REFERENCES students (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_spaced_repetition_items_tenant_id_student_id_competency_id UNIQUE (tenant_id, student_id, competency_id), 
	CONSTRAINT ck_spaced_repetition_items_schedule_range CHECK (interval_days >= 0 AND ease_factor >= 1 AND repetitions >= 0), 
	CONSTRAINT uq_spaced_repetition_items_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_spaced_repetition_items_competency_id_competencies FOREIGN KEY(competency_id) REFERENCES competencies (id), 
	CONSTRAINT fk_spaced_repetition_items_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_repetition_due ON spaced_repetition_items (tenant_id, student_id, due_at);

CREATE INDEX ix_spaced_repetition_items_tenant_id ON spaced_repetition_items (tenant_id);

CREATE TABLE teacher_classes (
	teacher_id UUID NOT NULL, 
	class_id UUID NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_teacher_classes PRIMARY KEY (id), 
	CONSTRAINT fk_teacher_classes_tenant_id_teachers FOREIGN KEY(tenant_id, teacher_id) REFERENCES teachers (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT fk_teacher_classes_tenant_id_classes FOREIGN KEY(tenant_id, class_id) REFERENCES classes (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_teacher_classes_tenant_id_teacher_id_class_id UNIQUE (tenant_id, teacher_id, class_id), 
	CONSTRAINT uq_teacher_classes_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_teacher_classes_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_teacher_classes_tenant_id ON teacher_classes (tenant_id);

CREATE TABLE ai_interactions (
	student_id UUID NOT NULL, 
	session_id UUID NOT NULL, 
	request_id UUID NOT NULL, 
	provider VARCHAR(20) NOT NULL, 
	model VARCHAR(120) NOT NULL, 
	prompt_template_version VARCHAR(80) NOT NULL, 
	hint_level INTEGER NOT NULL, 
	input_tokens INTEGER DEFAULT '0' NOT NULL, 
	output_tokens INTEGER DEFAULT '0' NOT NULL, 
	cost_eur NUMERIC(12, 6) DEFAULT '0' NOT NULL, 
	latency_ms INTEGER NOT NULL, 
	outcome VARCHAR(20) NOT NULL, 
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_ai_interactions PRIMARY KEY (id), 
	CONSTRAINT fk_ai_interactions_tenant_id_students FOREIGN KEY(tenant_id, student_id) REFERENCES students (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT fk_ai_interactions_tenant_id_learning_sessions FOREIGN KEY(tenant_id, session_id, student_id) REFERENCES learning_sessions (tenant_id, id, student_id), 
	CONSTRAINT uq_ai_interactions_tenant_id_request_id UNIQUE (tenant_id, request_id), 
	CONSTRAINT ck_ai_interactions_provider_values CHECK (provider IN ('local','cloud')), 
	CONSTRAINT ck_ai_interactions_outcome_values CHECK (outcome IN ('completed','blocked','failed','fallback')), 
	CONSTRAINT ck_ai_interactions_metrics_range CHECK (hint_level BETWEEN 0 AND 6 AND input_tokens >= 0 AND output_tokens >= 0 AND cost_eur >= 0 AND latency_ms >= 0), 
	CONSTRAINT ck_ai_interactions_retention_order CHECK (expires_at > created_at), 
	CONSTRAINT uq_ai_interactions_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_ai_interactions_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_ai_interactions_expires_at ON ai_interactions (expires_at);

CREATE INDEX ix_ai_interactions_tenant_id ON ai_interactions (tenant_id);

CREATE TABLE consent_records (
	student_id UUID NOT NULL, 
	guardian_id UUID NOT NULL, 
	purpose VARCHAR(80) NOT NULL, 
	policy_version VARCHAR(40) NOT NULL, 
	legal_basis VARCHAR(30) NOT NULL, 
	granted BOOLEAN NOT NULL, 
	recorded_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	withdrawn_at TIMESTAMP WITH TIME ZONE, 
	expires_at TIMESTAMP WITH TIME ZONE, 
	evidence_ciphertext BYTEA NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_consent_records PRIMARY KEY (id), 
	CONSTRAINT fk_consent_records_tenant_id_guardian_students FOREIGN KEY(tenant_id, guardian_id, student_id) REFERENCES guardian_students (tenant_id, guardian_id, student_id), 
	CONSTRAINT ck_consent_records_legal_basis_values CHECK (legal_basis IN ('consent','public_task','legal_obligation','contract')), 
	CONSTRAINT ck_consent_records_withdrawal_order CHECK (withdrawn_at IS NULL OR (granted AND withdrawn_at >= recorded_at)), 
	CONSTRAINT ck_consent_records_expiry_order CHECK (expires_at IS NULL OR expires_at > recorded_at), 
	CONSTRAINT uq_consent_records_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_consent_records_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_consent_lookup ON consent_records (tenant_id, student_id, purpose, recorded_at);

CREATE INDEX ix_consent_records_tenant_id ON consent_records (tenant_id);

CREATE TABLE content_reviews (
	lesson_version_id UUID, 
	exercise_version_id UUID, 
	reviewer_id UUID NOT NULL, 
	decision VARCHAR(20) NOT NULL, 
	reason_code VARCHAR(80) NOT NULL, 
	reviewed_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_content_reviews PRIMARY KEY (id), 
	CONSTRAINT fk_content_reviews_tenant_id_lesson_versions FOREIGN KEY(tenant_id, lesson_version_id) REFERENCES lesson_versions (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT fk_content_reviews_tenant_id_exercise_versions FOREIGN KEY(tenant_id, exercise_version_id) REFERENCES exercise_versions (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT fk_content_reviews_tenant_id_users FOREIGN KEY(tenant_id, reviewer_id) REFERENCES users (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT ck_content_reviews_exactly_one_target CHECK (num_nonnulls(lesson_version_id, exercise_version_id) = 1), 
	CONSTRAINT ck_content_reviews_decision_values CHECK (decision IN ('approved','rejected','changes_requested')), 
	CONSTRAINT uq_content_reviews_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_content_reviews_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_content_reviews_tenant_id ON content_reviews (tenant_id);

CREATE TABLE exercise_attempts (
	student_id UUID NOT NULL, 
	session_id UUID NOT NULL, 
	exercise_version_id UUID NOT NULL, 
	idempotency_key UUID NOT NULL, 
	started_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	submitted_at TIMESTAMP WITH TIME ZONE, 
	score NUMERIC(6, 5), 
	max_hint_level INTEGER DEFAULT '0' NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_exercise_attempts PRIMARY KEY (id), 
	CONSTRAINT fk_exercise_attempts_tenant_id_students FOREIGN KEY(tenant_id, student_id) REFERENCES students (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT fk_exercise_attempts_tenant_id_exercise_versions FOREIGN KEY(tenant_id, exercise_version_id) REFERENCES exercise_versions (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT fk_exercise_attempts_tenant_id_learning_sessions FOREIGN KEY(tenant_id, session_id, student_id) REFERENCES learning_sessions (tenant_id, id, student_id), 
	CONSTRAINT uq_exercise_attempts_tenant_id_idempotency_key UNIQUE (tenant_id, idempotency_key), 
	CONSTRAINT ck_exercise_attempts_score_range CHECK (score BETWEEN 0 AND 1), 
	CONSTRAINT ck_exercise_attempts_hint_range CHECK (max_hint_level BETWEEN 0 AND 6), 
	CONSTRAINT ck_exercise_attempts_time_order CHECK (submitted_at IS NULL OR submitted_at >= started_at), 
	CONSTRAINT ck_exercise_attempts_scored_submission CHECK (score IS NULL OR submitted_at IS NOT NULL), 
	CONSTRAINT uq_exercise_attempts_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_exercise_attempts_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_attempts_student_time ON exercise_attempts (tenant_id, student_id, started_at);

CREATE INDEX ix_exercise_attempts_tenant_id ON exercise_attempts (tenant_id);

CREATE TABLE exercise_competencies (
	exercise_version_id UUID NOT NULL, 
	competency_id UUID NOT NULL, 
	weight NUMERIC(6, 5) DEFAULT '1' NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_exercise_competencies PRIMARY KEY (id), 
	CONSTRAINT fk_exercise_competencies_tenant_id_exercise_versions FOREIGN KEY(tenant_id, exercise_version_id) REFERENCES exercise_versions (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_exercise_competencies_tenant_id_exercise_version_id__d9c0 UNIQUE (tenant_id, exercise_version_id, competency_id), 
	CONSTRAINT ck_exercise_competencies_weight_range CHECK (weight > 0 AND weight <= 1), 
	CONSTRAINT uq_exercise_competencies_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_exercise_competencies_competency_id_competencies FOREIGN KEY(competency_id) REFERENCES competencies (id), 
	CONSTRAINT fk_exercise_competencies_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_exercise_competencies_tenant_id ON exercise_competencies (tenant_id);

CREATE TABLE exercise_sources (
	exercise_version_id UUID NOT NULL, 
	source_id UUID NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_exercise_sources PRIMARY KEY (id), 
	CONSTRAINT fk_exercise_sources_tenant_id_exercise_versions FOREIGN KEY(tenant_id, exercise_version_id) REFERENCES exercise_versions (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT fk_exercise_sources_tenant_id_content_sources FOREIGN KEY(tenant_id, source_id) REFERENCES content_sources (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_exercise_sources_tenant_id_exercise_version_id_source_id UNIQUE (tenant_id, exercise_version_id, source_id), 
	CONSTRAINT uq_exercise_sources_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_exercise_sources_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_exercise_sources_tenant_id ON exercise_sources (tenant_id);

CREATE TABLE group_members (
	group_id UUID NOT NULL, 
	student_id UUID NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_group_members PRIMARY KEY (id), 
	CONSTRAINT fk_group_members_tenant_id_learning_groups FOREIGN KEY(tenant_id, group_id) REFERENCES learning_groups (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT fk_group_members_tenant_id_students FOREIGN KEY(tenant_id, student_id) REFERENCES students (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_group_members_tenant_id_group_id_student_id UNIQUE (tenant_id, group_id, student_id), 
	CONSTRAINT uq_group_members_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_group_members_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_group_members_tenant_id ON group_members (tenant_id);

CREATE TABLE hints (
	exercise_version_id UUID NOT NULL, 
	level INTEGER NOT NULL, 
	body JSONB NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_hints PRIMARY KEY (id), 
	CONSTRAINT fk_hints_tenant_id_exercise_versions FOREIGN KEY(tenant_id, exercise_version_id) REFERENCES exercise_versions (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_hints_tenant_id_exercise_version_id_level UNIQUE (tenant_id, exercise_version_id, level), 
	CONSTRAINT ck_hints_level_range CHECK (level BETWEEN 0 AND 6), 
	CONSTRAINT uq_hints_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_hints_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_hints_tenant_id ON hints (tenant_id);

CREATE TABLE lesson_competencies (
	lesson_version_id UUID NOT NULL, 
	competency_id UUID NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_lesson_competencies PRIMARY KEY (id), 
	CONSTRAINT fk_lesson_competencies_tenant_id_lesson_versions FOREIGN KEY(tenant_id, lesson_version_id) REFERENCES lesson_versions (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_lesson_competencies_tenant_id_lesson_version_id_comp_d47e UNIQUE (tenant_id, lesson_version_id, competency_id), 
	CONSTRAINT uq_lesson_competencies_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_lesson_competencies_competency_id_competencies FOREIGN KEY(competency_id) REFERENCES competencies (id), 
	CONSTRAINT fk_lesson_competencies_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_lesson_competencies_tenant_id ON lesson_competencies (tenant_id);

CREATE TABLE lesson_sources (
	lesson_version_id UUID NOT NULL, 
	source_id UUID NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_lesson_sources PRIMARY KEY (id), 
	CONSTRAINT fk_lesson_sources_tenant_id_lesson_versions FOREIGN KEY(tenant_id, lesson_version_id) REFERENCES lesson_versions (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT fk_lesson_sources_tenant_id_content_sources FOREIGN KEY(tenant_id, source_id) REFERENCES content_sources (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT uq_lesson_sources_tenant_id_lesson_version_id_source_id UNIQUE (tenant_id, lesson_version_id, source_id), 
	CONSTRAINT uq_lesson_sources_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_lesson_sources_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_lesson_sources_tenant_id ON lesson_sources (tenant_id);

CREATE TABLE answers (
	attempt_id UUID NOT NULL, 
	part_key VARCHAR(80) NOT NULL, 
	response_ciphertext BYTEA NOT NULL, 
	is_correct BOOLEAN, 
	feedback_code VARCHAR(80), 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_answers PRIMARY KEY (id), 
	CONSTRAINT fk_answers_tenant_id_exercise_attempts FOREIGN KEY(tenant_id, attempt_id) REFERENCES exercise_attempts (tenant_id, id) ON DELETE CASCADE, 
	CONSTRAINT uq_answers_tenant_id_attempt_id_part_key UNIQUE (tenant_id, attempt_id, part_key), 
	CONSTRAINT uq_answers_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_answers_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_answers_tenant_id ON answers (tenant_id);

CREATE TABLE safety_events (
	interaction_id UUID, 
	layer INTEGER NOT NULL, 
	category VARCHAR(80) NOT NULL, 
	severity VARCHAR(20) NOT NULL, 
	action VARCHAR(20) NOT NULL, 
	rule_version VARCHAR(80) NOT NULL, 
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_safety_events PRIMARY KEY (id), 
	CONSTRAINT fk_safety_events_tenant_id_ai_interactions FOREIGN KEY(tenant_id, interaction_id) REFERENCES ai_interactions (tenant_id, id) ON DELETE RESTRICT, 
	CONSTRAINT ck_safety_events_layer_range CHECK (layer BETWEEN 1 AND 10), 
	CONSTRAINT ck_safety_events_severity_values CHECK (severity IN ('info','low','medium','high','critical')), 
	CONSTRAINT ck_safety_events_action_values CHECK (action IN ('allow','redact','block','escalate')), 
	CONSTRAINT ck_safety_events_retention_order CHECK (expires_at > created_at), 
	CONSTRAINT uq_safety_events_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_safety_events_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
);

CREATE INDEX ix_safety_events_expires_at ON safety_events (expires_at);

CREATE INDEX ix_safety_events_tenant_id ON safety_events (tenant_id);
