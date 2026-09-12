-- Original editorial objectives aligned with science cycle 3, CM2 September 2026.
-- Internal codes, not official skill identifiers. Partial coverage; no publication of lessons.
INSERT INTO competencies(domain_id,subject_id,curriculum_level_id,code,label,description,objectives,common_errors,official_reference_url,programme_version,effective_from) VALUES
 ('00000000-0000-0000-0000-000000000704','00000000-0000-0000-0000-000000000204','00000000-0000-0000-0000-000000000102','CM2-SCI-LAB-MATIERE','L’eau dans tous ses états','Distinguer les états de l’eau et reconnaître un changement d’état réversible.','["Distinguer les états de l’eau et reconnaître un changement d’état réversible."]','["Croire que l’eau disparaît lorsqu’elle s’évapore.", "Confondre vapeur d’eau invisible et buée visible."]','https://www.education.gouv.fr/bo/2023/Hebdo25/MENE2314101A','sciences-2023-cm2-2026','2026-09-01'),
 ('00000000-0000-0000-0000-000000000704','00000000-0000-0000-0000-000000000204','00000000-0000-0000-0000-000000000102','CM2-SCI-LAB-DIGESTION','Le voyage des aliments','Localiser des transformations des aliments et relier la nutrition aux besoins des organes.','["Localiser des transformations des aliments et relier la nutrition aux besoins des organes."]','["Penser que tout se passe dans l’estomac.", "Croire que des morceaux entiers d’aliments circulent dans le sang."]','https://www.education.gouv.fr/bo/2023/Hebdo25/MENE2314101A','sciences-2023-cm2-2026','2026-09-01'),
 ('00000000-0000-0000-0000-000000000704','00000000-0000-0000-0000-000000000204','00000000-0000-0000-0000-000000000102','CM2-SCI-LAB-CIRCUITS','Mission : allumer la lampe','Prévoir l’effet d’une ouverture dans un circuit électrique simple à une boucle.','["Prévoir l’effet d’une ouverture dans un circuit électrique simple à une boucle."]','["Croire qu’un seul fil suffit pour relier la lampe à la pile.", "Penser que fermer l’interrupteur répare un autre fil débranché."]','https://www.education.gouv.fr/bo/2023/Hebdo25/MENE2314101A','sciences-2023-cm2-2026','2026-09-01'),
 ('00000000-0000-0000-0000-000000000704','00000000-0000-0000-0000-000000000204','00000000-0000-0000-0000-000000000102','CM2-SCI-LAB-TERRE','La Terre, le Soleil et les ombres','Situer la Terre dans le système solaire et comparer des ombres en changeant la position de la lumière.','["Situer la Terre dans le système solaire et comparer des ombres en changeant la position de la lumière."]','["Confondre le Soleil, une étoile, et la Terre, une planète.", "Déduire une saison d’une seule ombre sans connaître les conditions."]','https://www.education.gouv.fr/bo/2023/Hebdo25/MENE2314101A','sciences-2023-cm2-2026','2026-09-01')
ON CONFLICT(code,programme_version) DO NOTHING;

UPDATE competencies SET effective_until='2027-08-31' WHERE programme_version='sciences-2023-cm2-2026';
ALTER TABLE rag_documents DROP CONSTRAINT ck_rag_documents_subject_values;
ALTER TABLE rag_documents ADD CONSTRAINT ck_rag_documents_subject_values CHECK(subject IN ('francais','mathematiques','histoire','sciences'));

CREATE TABLE science_runs (
	student_id UUID NOT NULL, 
	request_id UUID NOT NULL, 
	chapter VARCHAR(20) NOT NULL, 
	setting VARCHAR(40) NOT NULL, 
	notebook_ciphertext BYTEA NOT NULL, 
	observation JSONB NOT NULL, 
	completed_at TIMESTAMP WITH TIME ZONE, 
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	tenant_id UUID NOT NULL, 
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_science_runs PRIMARY KEY (id), 
	CONSTRAINT fk_science_runs_tenant_id_students FOREIGN KEY(tenant_id, student_id) REFERENCES students (tenant_id, id) ON DELETE CASCADE, 
	CONSTRAINT uq_science_runs_tenant_id_student_id_request_id UNIQUE (tenant_id, student_id, request_id), 
	CONSTRAINT ck_science_runs_chapter_values CHECK (chapter IN ('matiere','digestion','circuits','terre')), 
	CONSTRAINT uq_science_runs_tenant_id_id UNIQUE (tenant_id, id), 
	CONSTRAINT fk_science_runs_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;
CREATE INDEX ix_science_runs_tenant_id ON science_runs (tenant_id);
ALTER TABLE science_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE science_runs FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON science_runs USING(tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid) WITH CHECK(tenant_id=NULLIF(current_setting('app.tenant_id',true),'')::uuid);
CREATE TRIGGER t90_updated_at BEFORE UPDATE ON science_runs FOR EACH ROW EXECUTE FUNCTION edu_touch_updated_at();
GRANT SELECT,INSERT,UPDATE,DELETE ON science_runs TO edu_assessment;
GRANT SELECT,DELETE ON science_runs TO edu_notification;
