import os
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import URL, create_engine, text


@pytest.fixture
def db():
    if os.getenv("EDU_TEST_INTEGRATION") != "1":
        pytest.skip("Activer EDU_TEST_INTEGRATION=1 sur le réseau Compose")
    password = Path("/run/secrets/postgres_password").read_text().strip()
    engine = create_engine(URL.create("postgresql+psycopg", username="postgres", password=password,
        host="postgres", database=os.getenv("EDU_TEST_DB_NAME", "educapilote")))
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            yield connection
        finally:
            transaction.rollback()
    engine.dispose()


@pytest.fixture
def identities(db):
    tenant, other = uuid4(), uuid4()
    author, reviewer, guardian_user, student_user, student2_user = [uuid4() for _ in range(5)]
    for tid in [tenant, other]:
        db.execute(text("INSERT INTO tenants(id,name) VALUES (:id,'Test technique temporaire')"), {"id": tid})
    for uid in [author, reviewer, guardian_user, student_user, student2_user]:
        db.execute(text("INSERT INTO users(id,tenant_id,login,status) VALUES (:id,:tenant,:login,'active')"),
            {"id": uid, "tenant": tenant, "login": str(uid)})
    db.execute(text("INSERT INTO user_roles(tenant_id,user_id,role) VALUES (:tenant,:id,'teacher')"), {"tenant": tenant, "id": reviewer})
    students = [uuid4(), uuid4()]
    for sid, uid in zip(students, [student_user, student2_user]):
        db.execute(text("INSERT INTO students(id,tenant_id,user_id,pseudonym,curriculum_level_id) VALUES (:id,:tenant,:user,'Test','00000000-0000-0000-0000-000000000101')"),
            {"id": sid, "tenant": tenant, "user": uid})
    db.execute(text("SELECT set_config('app.tenant_id', :tenant, true)"), {"tenant": str(tenant)})
    return {"tenant": tenant, "other": other, "author": author, "reviewer": reviewer,
        "guardian_user": guardian_user, "student": students[0], "student2": students[1]}
