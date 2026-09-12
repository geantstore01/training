from pathlib import Path
import os
from uuid import uuid4

import pytest
from sqlalchemy import URL, create_engine, inspect, text
from sqlalchemy.exc import DBAPIError
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.config import Config
from alembic.script import ScriptDirectory

from shared.db.models import Base

pytestmark = pytest.mark.integration


def fails(db, sql, params=None, code="23514"):
    with pytest.raises(DBAPIError) as caught:
        with db.begin_nested():
            db.execute(text(sql), params or {})
    assert caught.value.orig.sqlstate == code


def role(db, name):
    assert name in {"edu_user", "edu_auth", "edu_content", "edu_admin", "edu_curriculum", "edu_tutor", "edu_assessment"}
    db.exec_driver_sql(f"SET LOCAL ROLE {name}")


def test_schema_installed_and_vector(db):
    inspector = inspect(db)
    assert set(Base.metadata.tables) <= set(inspector.get_table_names())
    assert db.scalar(text("SELECT extversion FROM pg_extension WHERE extname='vector'"))
    assert db.scalar(text("SELECT version_num FROM alembic_version")) == ScriptDirectory.from_config(Config("alembic.ini")).get_current_head()
    tables = db.execute(text("SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class JOIN pg_namespace ON pg_namespace.oid=relnamespace WHERE nspname='public' AND relkind='r'"))
    for name, rls, force in tables:
        if name in Base.metadata.tables and (name == "tenants" or "tenant_id" in Base.metadata.tables[name].c):
            assert rls and force, name


def test_real_runtime_login_has_no_superpowers(db):
    password = Path("/run/secrets/db_user").read_text().strip()
    engine = create_engine(URL.create("postgresql+psycopg", username="edu_user", password=password, host="postgres", database=os.getenv("EDU_TEST_DB_NAME", "educapilote")))
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT current_user")) == "edu_user"
        assert connection.execute(text("SELECT rolsuper, rolbypassrls, rolcreaterole FROM pg_roles WHERE rolname=current_user")).one() == (False, False, False)
        assert connection.scalar(text("SELECT count(*) FROM users")) == 0
    engine.dispose()


def test_migration_matches_sqlalchemy_metadata(db):
    context = MigrationContext.configure(db, opts={"compare_type": True})
    assert compare_metadata(context, Base.metadata) == []


def test_pgvector_and_french_search_are_operational(db, identities):
    source = db.scalar(text("INSERT INTO content_sources(tenant_id,title,url,publisher,license,checksum_sha256,retrieved_at) VALUES (:tenant,'Test','https://example.invalid','Test','Test',repeat('a',64),now()) RETURNING id"), identities)
    db.execute(text("INSERT INTO content_chunks(tenant_id,source_id,ordinal,body,embedding,embedding_model) VALUES (:tenant,:source,0,'Les fractions et les nombres',CAST(:vector AS vector),'test-768')"),
        {**identities, "source": source, "vector": str([1.0] + [0.0] * 767)})
    assert db.scalar(text("SELECT count(*) FROM content_chunks WHERE search_vector @@ plainto_tsquery('french','fraction')")) == 1
    assert db.scalar(text("SELECT embedding <=> embedding FROM content_chunks LIMIT 1")) == 0.0


def test_rls_read_write_and_tenant_switch(db, identities):
    role(db, "edu_user")
    assert db.scalar(text("SELECT count(*) FROM users")) == 5
    fails(db, "INSERT INTO users(tenant_id,login) VALUES (:tenant,'forbidden')", {"tenant": identities["other"]}, "42501")
    db.execute(text("SELECT set_config('app.tenant_id', :tenant, true)"), {"tenant": str(identities["other"])})
    assert db.scalar(text("SELECT count(*) FROM users")) == 0
    assert db.execute(text("UPDATE users SET status='locked' WHERE id=:id"), {"id": identities["author"]}).rowcount == 0
    db.execute(text("SELECT set_config('app.tenant_id', '', true)"))
    assert db.scalar(text("SELECT count(*) FROM users")) == 0


def test_set_local_context_cleared_after_transaction(db, identities):
    password = Path("/run/secrets/db_user").read_text().strip()
    engine = create_engine(URL.create("postgresql+psycopg", username="edu_user", password=password, host="postgres", database=os.getenv("EDU_TEST_DB_NAME", "educapilote")), pool_size=1, max_overflow=0)
    with engine.begin() as c:
        c.execute(text("SELECT set_config('app.tenant_id', :tenant, true)"), {"tenant": str(identities["tenant"])})
    with engine.connect() as c:
        assert c.scalar(text("SELECT NULLIF(current_setting('app.tenant_id', true),'')")) is None
    engine.dispose()


def test_cross_tenant_fk_rejected_even_as_owner(db, identities):
    fails(db, "INSERT INTO teachers(tenant_id,user_id,display_name) VALUES (:tenant,:user,'Test')",
        {"tenant": identities["other"], "user": identities["author"]}, "23503")


def test_runtime_cannot_ddl_or_read_other_service(db, identities):
    role(db, "edu_auth")
    fails(db, "CREATE TABLE forbidden_table(id int)", code="42501")
    fails(db, "SELECT * FROM answers", code="42501")
    fails(db, "TRUNCATE users", code="42501")


def test_audit_and_reviews_append_only(db, identities):
    role(db, "edu_admin")
    fails(db, "DELETE FROM audit_logs", code="42501")
    fails(db, "UPDATE content_reviews SET decision='approved'", code="42501")


def create_version(db, ids, exercise=False):
    item, version = uuid4(), uuid4()
    parent = "exercises" if exercise else "lessons"
    db.execute(text(f"INSERT INTO {parent}(id,tenant_id,slug,author_id) VALUES (:id,:tenant,:slug,:author)"),
        {"id": item, "tenant": ids["tenant"], "slug": str(item), "author": ids["author"]})
    if exercise:
        db.execute(text("INSERT INTO exercise_versions(id,tenant_id,exercise_id,version,kind,prompt,answer_spec,validator_name,validator_version,difficulty) VALUES (:id,:tenant,:parent,1,'integer','{}','{}','integer','1',1)"),
            {"id": version, "tenant": ids["tenant"], "parent": item})
    else:
        db.execute(text("INSERT INTO lesson_versions(id,tenant_id,lesson_id,version,title,body) VALUES (:id,:tenant,:parent,1,'Test','{}')"),
            {"id": version, "tenant": ids["tenant"], "parent": item})
    return version


def approve(db, ids, version, exercise=False):
    table = "exercise_versions" if exercise else "lesson_versions"
    column = "exercise_version_id" if exercise else "lesson_version_id"
    state = "in_review" if exercise else "pending_review"
    db.execute(text(f"UPDATE {table} SET status=:state WHERE id=:id"), {"id": version, "state": state})
    db.execute(text(f"INSERT INTO content_reviews(tenant_id,{column},reviewer_id,decision,reason_code) VALUES (:tenant,:id,:reviewer,'approved','checked')"),
        {"tenant": ids["tenant"], "id": version, "reviewer": ids["reviewer"]})
    statement = f"UPDATE {table} SET status='published',published_at=clock_timestamp() WHERE id=:id" if exercise else "UPDATE lesson_versions SET status='approved' WHERE id=:id"
    db.execute(text(statement), {"id": version})


def test_human_approval_and_immutable_content(db, identities):
    role(db, "edu_content")
    version = create_version(db, identities)
    fails(db, "UPDATE lesson_versions SET status='approved' WHERE id=:id", {"id": version})
    role(db, "edu_admin")
    approve(db, identities, version)
    role(db, "edu_content")
    fails(db, "UPDATE lesson_versions SET title='Changed' WHERE id=:id", {"id": version})
    fails(db, "UPDATE lesson_versions SET status='draft',published_at=NULL WHERE id=:id", {"id": version})


def test_author_cannot_approve_own_content(db, identities):
    version = create_version(db, identities)
    db.execute(text("UPDATE lesson_versions SET status='pending_review' WHERE id=:id"), {"id": version})
    fails(db, "INSERT INTO content_reviews(tenant_id,lesson_version_id,reviewer_id,decision,reason_code) VALUES (:tenant,:id,:reviewer,'approved','checked')",
        {"tenant": identities["tenant"], "id": version, "reviewer": identities["author"]})


def test_stale_approval_not_reused(db, identities):
    version = create_version(db, identities)
    db.execute(text("UPDATE lesson_versions SET status='pending_review' WHERE id=:id"), {"id": version})
    db.execute(text("INSERT INTO content_reviews(tenant_id,lesson_version_id,reviewer_id,decision,reason_code) VALUES (:tenant,:id,:reviewer,'approved','checked')"),
        {"tenant": identities["tenant"], "id": version, "reviewer": identities["reviewer"]})
    db.execute(text("INSERT INTO content_reviews(tenant_id,lesson_version_id,reviewer_id,decision,reason_code) VALUES (:tenant,:id,:reviewer,'changes_requested','revise')"),
        {"tenant": identities["tenant"], "id": version, "reviewer": identities["reviewer"]})
    for status in ["draft", "pending_review"]:
        db.execute(text("UPDATE lesson_versions SET status=:status WHERE id=:id"), {"id": version, "status": status})
    fails(db, "UPDATE lesson_versions SET status='approved' WHERE id=:id", {"id": version})


def test_published_hints_immutable_and_tutor_no_answer_spec(db, identities):
    version = create_version(db, identities, exercise=True)
    db.execute(text("INSERT INTO hints(tenant_id,exercise_version_id,level,body) VALUES (:tenant,:id,1,'{}')"), {"tenant": identities["tenant"], "id": version})
    approve(db, identities, version, exercise=True)
    fails(db, "UPDATE hints SET body='{\"text\":\"changed\"}' WHERE exercise_version_id=:id", {"id": version})
    role(db, "edu_tutor")
    assert db.scalar(text("SELECT count(prompt) FROM exercise_versions")) == 1
    fails(db, "SELECT answer_spec FROM exercise_versions", code="42501")


def test_attempt_student_matches_session(db, identities):
    version = create_version(db, identities, exercise=True)
    approve(db, identities, version, exercise=True)
    session = db.scalar(text("INSERT INTO learning_sessions(tenant_id,student_id) VALUES (:tenant,:student) RETURNING id"), identities)
    fails(db, "INSERT INTO exercise_attempts(tenant_id,student_id,session_id,exercise_version_id,idempotency_key) VALUES (:tenant,:student2,:session,:version,:key)",
        {**identities, "session": session, "version": version, "key": uuid4()}, "23503")


def test_draft_exercise_cannot_be_attempted(db, identities):
    version = create_version(db, identities, exercise=True)
    session = db.scalar(text("INSERT INTO learning_sessions(tenant_id,student_id) VALUES (:tenant,:student) RETURNING id"), identities)
    fails(db, "INSERT INTO exercise_attempts(tenant_id,student_id,session_id,exercise_version_id,idempotency_key) VALUES (:tenant,:student,:session,:version,:key)",
        {**identities, "session": session, "version": version, "key": uuid4()})


def test_consent_requires_verified_authority(db, identities):
    guardian = db.scalar(text("INSERT INTO guardians(tenant_id,user_id) VALUES (:tenant,:guardian_user) RETURNING id"), identities)
    db.execute(text("INSERT INTO guardian_students(tenant_id,guardian_id,student_id,relationship) VALUES (:tenant,:guardian,:student,'parent')"), {**identities, "guardian": guardian})
    statement = "INSERT INTO consent_records(tenant_id,student_id,guardian_id,recorded_by,event_type,purpose,policy_version,legal_basis,granted,evidence_ciphertext) VALUES (:tenant,:student,:guardian,:guardian_user,'grant','ai_local','1','consent',true,decode('abcd','hex'))"
    fails(db, statement, {**identities, "guardian": guardian})
    db.execute(text("UPDATE guardians SET verified_at=now() WHERE id=:id"), {"id": guardian})
    db.execute(text("UPDATE guardian_students SET authority_verified_at=now() WHERE guardian_id=:id"), {"id": guardian})
    db.execute(text("INSERT INTO user_roles(tenant_id,user_id,role) VALUES (:tenant,:guardian_user,'parent')"), identities)
    role(db, "edu_user")
    db.execute(text(statement), {**identities, "guardian": guardian})
    fails(db, "UPDATE consent_records SET granted=false", code="42501")
    fails(db, "DELETE FROM consent_records", code="42501")


def test_prerequisite_cycle(db):
    subject = db.scalar(text("INSERT INTO subjects(code,name) VALUES (:code,'Test') RETURNING id"), {"code": str(uuid4())})
    ids = []
    for _ in range(3):
        ids.append(db.scalar(text("INSERT INTO competencies(subject_id,curriculum_level_id,code,label,description,official_reference_url,programme_version,effective_from) VALUES (:subject,'00000000-0000-0000-0000-000000000101',:code,'Test','Test','https://example.invalid','test',current_date) RETURNING id"), {"subject": subject, "code": str(uuid4())}))
    for a, b in zip(ids, ids[1:]):
        db.execute(text("INSERT INTO competency_prerequisites(competency_id,prerequisite_id) VALUES (:a,:b)"), {"a": a, "b": b})
    fails(db, "INSERT INTO competency_prerequisites(competency_id,prerequisite_id) VALUES (:a,:b)", {"a": ids[-1], "b": ids[0]})


def test_mastery_probability_range(db, identities):
    # CHECK est évalué avant la FK : une valeur probabiliste invalide est refusée.
    fails(db, "INSERT INTO mastery_records(tenant_id,student_id,competency_id,probability,algorithm_version) VALUES (:tenant,:student,:competency,1.5,'test')",
        {**identities, "competency": uuid4()})
