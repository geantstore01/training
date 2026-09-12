from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
import os
from pathlib import Path
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
import pytest
from redis.exceptions import NoPermissionError
from sqlalchemy import URL, create_engine, text
from sqlalchemy.exc import IntegrityError

from shared.config import Settings
from shared.security.passwords import hash_password
from shared.security.sessions import session_key, unpack_refresh
from shared.service_loader import load_service

pytestmark = pytest.mark.integration
POLICY = "2026-09-v1"


class Lab:
    def __init__(self, engine, clients):
        self.engine, self.clients = engine, clients
        self.school, self.other = uuid4(), uuid4()
        self.sessions = []
        self.password = "Synthetic-test-passphrase-42"
        self.admin_id, self.other_id = uuid4(), uuid4()
        hashed = hash_password(self.password)
        with engine.begin() as connection:
            for school, user in [(self.school, self.admin_id), (self.other, self.other_id)]:
                connection.execute(text("INSERT INTO tenants(id,name) VALUES (:id,'École de test')"), {"id": school})
                connection.execute(text("INSERT INTO schools(id,tenant_id,name) VALUES (:id,:id,'École des Étoiles')"), {"id": school})
                connection.execute(text("INSERT INTO users(id,tenant_id,login,password_hash,status) VALUES (:id,:school,'admin',:hash,'active')"), {"id": user, "school": school, "hash": hashed})
                connection.execute(text("INSERT INTO user_roles(tenant_id,user_id,role) VALUES (:school,:id,'school_admin')"), {"id": user, "school": school})
        self.admin = self.login("admin", self.school)

    def login(self, login, school=None, password=None):
        response = self.clients["auth"].post("/login", json={"school_id": str(school or self.school), "login": login, "password": password or self.password})
        assert response.status_code == 200, response.text
        pair = response.json()
        self.sessions.append(unpack_refresh(pair["refresh_token"]))
        return pair

    @staticmethod
    def headers(pair):
        return {"Authorization": "Bearer " + pair["access_token"]}

    def create(self, role="student"):
        login = "u" + uuid4().hex
        payload = {"login": login, "password": self.password, "role": role}
        if role == "student":
            payload["student"] = {"first_name": "Inès", "last_name": "Durand", "pseudonym": "Explorateur", "level": "CM1"}
        if role == "teacher":
            payload["display_name"] = "Enseignant de test"
        response = self.clients["user"].post("/accounts", json=payload, headers=self.headers(self.admin))
        assert response.status_code == 201, response.text
        return response.json()

    def link(self, parent, student):
        response = self.clients["user"].post("/guardian-links", json={"guardian_id": parent["guardian_id"],
            "student_id": student["student_id"], "relationship": "parent", "verification_reference": "TEST-VERIFICATION-NOT-A-REAL-PERSON"}, headers=self.headers(self.admin))
        assert response.status_code == 201, response.text
        return response.json()


@pytest.fixture
def lab():
    database = os.getenv("EDU_TEST_DB_NAME", "")
    if os.getenv("EDU_TEST_INTEGRATION") != "1" or not database.startswith(("edu_module2_test_", "edu_module3_test_", "edu_module4_test_", "edu_module56_test_", "edu_module78_test_")):
        pytest.skip("Exécuter scripts/test_module2.sh : base jetable obligatoire")
    password = Path("/run/secrets/postgres_password").read_text().strip()
    engine = create_engine(URL.create("postgresql+psycopg", username="postgres", password=password, host="postgres", database=database))
    with ExitStack() as stack:
        clients = {}
        for name in ["auth", "user", "safety"]:
            config = Settings(service_name=f"{name}-service", db_name=database, db_user=f"edu_{name}",
                db_password_file=Path(f"/run/secrets/db_{name}"), redis_username=f"edu_{name}", redis_db=15,
                redis_password_file=Path(f"/run/secrets/redis_{name}"))
            clients[name] = stack.enter_context(TestClient(load_service(f"{name}-service").build_app(config), client=(str(uuid4()), 50000)))
        result = Lab(engine, clients)
        try:
            yield result
        finally:
            for sid in result.sessions:
                clients["auth"].app.state.cache.delete(session_key(sid))
    engine.dispose()


def test_refresh_rotation_and_replay_revokes_access(lab):
    auth, user = lab.clients["auth"], lab.clients["user"]
    old = lab.admin
    rotated = auth.post("/refresh", json={"refresh_token": old["refresh_token"]})
    assert rotated.status_code == 200, rotated.text
    assert rotated.json()["refresh_token"] != old["refresh_token"]
    assert user.get("/me", headers=lab.headers(rotated.json())).status_code == 200
    assert auth.post("/refresh", json={"refresh_token": old["refresh_token"]}).status_code == 401
    assert user.get("/me", headers=lab.headers(rotated.json())).status_code == 401


def test_concurrent_refresh_has_one_winner_and_revokes_family(lab):
    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda _: lab.clients["auth"].post("/refresh", json={"refresh_token": lab.admin["refresh_token"]}), range(2)))
    assert sorted(r.status_code for r in responses) == [200, 401], [r.text for r in responses]
    winner = next(r.json() for r in responses if r.status_code == 200)
    assert lab.clients["user"].get("/me", headers=lab.headers(winner)).status_code == 401


def test_forged_refresh_does_not_revoke_valid_family(lab):
    sid = unpack_refresh(lab.admin["refresh_token"])
    response = lab.clients["auth"].post("/refresh", json={"refresh_token": str(sid)+"."+"x"*64})
    assert response.status_code == 401
    assert lab.clients["user"].get("/me", headers=lab.headers(lab.admin)).status_code == 200
    record = lab.clients["auth"].app.state.sessions.read(sid)
    assert lab.admin["refresh_token"] not in str(record)


def test_logout_and_logout_all_are_immediate(lab):
    other = lab.login("admin")
    auth, user = lab.clients["auth"], lab.clients["user"]
    assert auth.post("/logout", headers=lab.headers(lab.admin)).status_code == 204
    assert user.get("/me", headers=lab.headers(lab.admin)).status_code == 401
    assert user.get("/me", headers=lab.headers(other)).status_code == 200
    third = lab.login("admin")
    assert auth.post("/logout-all", headers=lab.headers(other)).status_code == 204
    for pair in [other, third]:
        assert user.get("/me", headers=lab.headers(pair)).status_code == 401
        assert auth.post("/refresh", json={"refresh_token": pair["refresh_token"]}).status_code == 401


def test_password_change_revokes_sessions_and_rehashes(lab):
    response = lab.clients["auth"].post("/password", headers=lab.headers(lab.admin),
        json={"current_password": lab.password, "new_password": "A-new-test-passphrase-99"})
    assert response.status_code == 204, response.text
    assert lab.clients["user"].get("/me", headers=lab.headers(lab.admin)).status_code == 401
    assert lab.clients["auth"].post("/login", json={"school_id": str(lab.school), "login": "admin", "password": lab.password}).status_code == 401
    assert lab.login("admin", password="A-new-test-passphrase-99")["access_token"]


def test_login_failure_is_generic_and_rate_limited(lab):
    auth = lab.clients["auth"]
    payload = {"school_id": str(lab.school), "login": "missing", "password": "incorrect"}
    missing = auth.post("/login", json=payload)
    wrong = auth.post("/login", json={**payload, "login": "admin"})
    assert missing.status_code == wrong.status_code == 401 and missing.json() == wrong.json()
    codes = [auth.post("/login", json=payload).status_code for _ in range(5)]
    assert codes[-1] == 429


def test_cross_school_isolation_and_role_escalation_denied(lab):
    student = lab.create()
    other = lab.login("admin", lab.other)
    user = lab.clients["user"]
    assert user.get(f"/students/{student['student_id']}", headers=lab.headers(other)).status_code == 404
    parent = lab.create("parent")
    parent_token = lab.login(parent["login"])
    assert user.post("/accounts", headers=lab.headers(parent_token), json={"login": "forbidden", "password": lab.password, "role": "teacher", "display_name": "Test"}).status_code == 403
    for role in ["sys_admin", "school_admin"]:
        assert user.post("/accounts", headers=lab.headers(lab.admin), json={"login": "forbidden", "password": lab.password, "role": role}).status_code == 403
    assert user.post("/accounts", headers=lab.headers(lab.admin), json={"school_id": str(lab.other), "login": "forbidden", "password": lab.password, "role": "parent"}).status_code == 422


def test_verified_parent_link_and_encrypted_identity(lab):
    student, parent, stranger = lab.create(), lab.create("parent"), lab.create("parent")
    parent_token, stranger_token = lab.login(parent["login"]), lab.login(stranger["login"])
    path = f"/students/{student['student_id']}"
    user = lab.clients["user"]
    assert user.get(path, headers=lab.headers(parent_token)).status_code == 404
    link = lab.link(parent, student)
    assert user.get(path, headers=lab.headers(parent_token)).status_code == 200
    assert user.get(path, headers=lab.headers(stranger_token)).status_code == 404
    assert user.get(path+"/identity", headers=lab.headers(parent_token)).json()["last_name"] == "Durand"
    with lab.engine.connect() as connection:
        ciphertext = connection.scalar(text("SELECT identity_ciphertext FROM students WHERE id=:id"), {"id": student["student_id"]})
        assert b"Durand" not in ciphertext
    assert user.post(f"/guardian-links/{link['id']}/revoke", headers=lab.headers(lab.admin)).status_code == 200
    assert user.get(path, headers=lab.headers(parent_token)).status_code == 404


def test_consent_history_assent_and_withdrawal_gate_safety(lab):
    student, parent = lab.create(), lab.create("parent")
    lab.link(parent, student)
    child_token, parent_token = lab.login(student["login"]), lab.login(parent["login"])
    user, safety = lab.clients["user"], lab.clients["safety"]
    path = f"/students/{student['student_id']}"
    grant = user.post(path+"/consents", headers=lab.headers(parent_token), json={"purpose": "ai_local", "policy_version": POLICY, "granted": True, "understood": True})
    assert grant.status_code == 201, grant.text
    assert user.get(path+"/permissions", headers=lab.headers(parent_token)).json()["ai_local"] is False
    assent = user.post("/me/assents", headers=lab.headers(child_token), json={"purpose": "ai_local", "policy_version": POLICY, "agreed": True})
    assert assent.status_code == 201, assent.text
    assert user.get(path+"/permissions", headers=lab.headers(parent_token)).json()["ai_local"] is True
    checked = safety.post("/analyze", headers=lab.headers(child_token), json={"text": "Je m'appelle Inès Durand et je veux comprendre les fractions."})
    assert checked.status_code == 200, checked.text
    assert checked.json()["decision"] == "redact" and "Durand" not in checked.json()["sanitized_text"]
    withdrawal = user.post(path+"/consents/withdraw", headers=lab.headers(parent_token), json={"purpose": "ai_local", "policy_version": POLICY})
    assert withdrawal.status_code == 201, withdrawal.text
    assert withdrawal.json()["supersedes_id"] == grant.json()["id"] and withdrawal.json()["revision"] == 2
    history = user.get(path+"/consents", headers=lab.headers(parent_token)).json()
    assert [event["granted"] for event in history] == [False, True]
    checked = safety.post("/analyze", headers=lab.headers(child_token), json={"text": "Explique les fractions."})
    assert checked.json()["decision"] == "block" and checked.json()["sanitized_text"] is None
    assert "consent_required" in checked.json()["layers"][-1]["codes"]


def test_students_cannot_consent_as_parent_and_cannot_spoof_context(lab):
    student, other = lab.create(), lab.create()
    token = lab.login(student["login"])
    response = lab.clients["user"].post(f"/students/{student['student_id']}/consents", headers=lab.headers(token),
        json={"purpose": "ai_local", "policy_version": POLICY, "granted": True, "understood": True})
    assert response.status_code == 403
    assert lab.clients["safety"].post("/analyze", headers=lab.headers(token), json={"text": "Bonjour", "student_id": other["student_id"]}).status_code == 404


def test_teacher_only_reads_assigned_students(lab):
    student, other, teacher = lab.create(), lab.create(), lab.create("teacher")
    token = lab.login(teacher["login"])
    path = f"/students/{student['student_id']}"
    assert lab.clients["user"].get(path, headers=lab.headers(token)).status_code == 404
    with lab.engine.begin() as connection:
        class_id = uuid4()
        connection.execute(text("INSERT INTO classes(id,tenant_id,school_id,name,academic_year) VALUES (:id,:school,:school,'Test',2026)"), {"id": class_id, "school": lab.school})
        connection.execute(text("INSERT INTO teacher_classes(tenant_id,teacher_id,class_id) VALUES (:school,:teacher,:class)"), {"school": lab.school, "teacher": teacher["teacher_id"], "class": class_id})
        connection.execute(text("INSERT INTO enrollments(tenant_id,student_id,class_id,starts_on) VALUES (:school,:student,:class,current_date-10)"), {"school": lab.school, "student": student["student_id"], "class": class_id})
    assert lab.clients["user"].get(path, headers=lab.headers(token)).status_code == 200
    assert lab.clients["user"].get(f"/students/{other['student_id']}", headers=lab.headers(token)).status_code == 404
    with lab.engine.begin() as connection:
        connection.execute(text("UPDATE enrollments SET ends_on=current_date-1 WHERE student_id=:id"), {"id": student["student_id"]})
    assert lab.clients["user"].get(path, headers=lab.headers(token)).status_code == 404


def test_account_lock_and_database_roles_are_revalidated(lab):
    account = lab.create("content_creator")
    token = lab.login(account["login"])
    response = lab.clients["user"].patch(f"/accounts/{account['id']}", headers=lab.headers(lab.admin), json={"status": "locked"})
    assert response.status_code == 200, response.text
    assert lab.clients["user"].get("/me", headers=lab.headers(token)).status_code == 401
    assert lab.clients["auth"].post("/refresh", json={"refresh_token": token["refresh_token"]}).status_code == 401
    with lab.engine.begin() as connection:
        connection.execute(text("UPDATE user_roles SET role='content_creator' WHERE user_id=:id"), {"id": lab.admin_id})
    assert lab.clients["user"].get("/me", headers=lab.headers(lab.admin)).status_code == 401


def test_redis_acl_rejects_session_writes_from_user_service(lab):
    cache = lab.clients["user"].app.state.cache
    key = session_key(unpack_refresh(lab.admin["refresh_token"]))
    assert cache.hgetall(key)
    with pytest.raises(NoPermissionError):
        cache.incr(key)
    with pytest.raises(NoPermissionError):
        cache.hset(key, "revoked", "0")


def test_safety_blocks_anonymous_and_logs_only_codes(lab):
    safety = lab.clients["safety"]
    assert safety.post("/analyze", json={"text": "Bonjour"}).status_code == 401
    response = safety.post("/analyze", headers=lab.headers(lab.admin), json={"text": "Je veux me suicider"})
    assert response.status_code == 200, response.text
    assert response.json()["requires_adult_support"] and response.json()["sanitized_text"] is None
    with lab.engine.connect() as connection:
        rows = connection.execute(text("SELECT category,action FROM safety_events WHERE request_id=:id"), {"id": response.json()["request_id"]}).all()
        assert rows and all("suicider" not in str(row) for row in rows)


def test_system_admin_provisions_school_without_cross_scope_read(lab):
    with lab.engine.begin() as connection:
        connection.execute(text("UPDATE user_roles SET role='sys_admin' WHERE user_id=:id"), {"id": lab.admin_id})
        connection.execute(text("UPDATE users SET auth_version=auth_version+1 WHERE id=:id"), {"id": lab.admin_id})
    token = lab.login("admin")
    response = lab.clients["user"].post("/schools", headers=lab.headers(token), json={"name": "Nouvelle école de test", "admin": {"login": "newadmin", "password": lab.password, "role": "school_admin"}})
    assert response.status_code == 201, response.text
    new_school = response.json()["school_id"]
    new_token = lab.login("newadmin", new_school)
    assert lab.clients["user"].get("/me", headers=lab.headers(new_token)).json()["school_id"] == new_school


def test_expired_redis_session_is_denied(lab):
    key = session_key(unpack_refresh(lab.admin["refresh_token"]))
    lab.clients["auth"].app.state.cache.expire(key, 0)
    assert lab.clients["user"].get("/me", headers=lab.headers(lab.admin)).status_code == 401
    assert lab.clients["auth"].post("/refresh", json={"refresh_token": lab.admin["refresh_token"]}).status_code == 401


def test_second_parent_and_child_withdrawal_are_effective(lab):
    student, first, second = lab.create(), lab.create("parent"), lab.create("parent")
    lab.link(first, student)
    lab.link(second, student)
    child, parent1, parent2 = lab.login(student["login"]), lab.login(first["login"]), lab.login(second["login"])
    user = lab.clients["user"]
    path = f"/students/{student['student_id']}"
    notice = {"purpose": "ai_local", "policy_version": POLICY}
    user.post("/me/assents", headers=lab.headers(child), json={**notice, "agreed": True}).raise_for_status()
    for parent, expected in [(parent1, False), (parent2, True)]:
        user.post(path+"/consents", headers=lab.headers(parent), json={**notice, "granted": True, "understood": True}).raise_for_status()
        assert user.get(path+"/permissions", headers=lab.headers(child)).json()["ai_local"] is expected
    user.post("/me/assents", headers=lab.headers(child), json={**notice, "agreed": False}).raise_for_status()
    assert user.get(path+"/permissions", headers=lab.headers(child)).json()["ai_local"] is False
    with lab.engine.begin() as connection:
        with pytest.raises(IntegrityError):
            with connection.begin_nested():
                connection.execute(text("UPDATE consent_records SET granted=false WHERE student_id=:id"), {"id": student["student_id"]})


def test_ner_failure_never_returns_unfiltered_text(lab, monkeypatch):
    def unavailable(*args, **kwargs):
        raise RuntimeError("Synthetic failure in test only")
    monkeypatch.setattr(lab.clients["safety"].app.state.safety, "analyze", unavailable)
    response = lab.clients["safety"].post("/analyze", headers=lab.headers(lab.admin), json={"text": "Inès Durand habite au 12 rue des Lilas"})
    assert response.status_code == 503 and "Durand" not in response.text


def test_invalid_redis_credentials_fail_closed(lab, tmp_path):
    wrong = tmp_path / "bad-redis-password"
    wrong.write_text("invalid-password-for-test")
    settings = lab.clients["user"].app.state.settings.model_copy(update={"redis_password_file": wrong})
    with TestClient(load_service("user-service").build_app(settings)) as client:
        assert client.get("/health/ready").status_code == 503
        assert client.get("/me", headers=lab.headers(lab.admin)).status_code == 503


def test_operator_bootstrap_works_with_restricted_sql_role(lab):
    from scripts.bootstrap_school import provision
    school = provision(lab.clients["user"].app.state.engine, "École bootstrap test", "bootstrap", lab.password, system_admin=True)
    token = lab.login("bootstrap", school)
    assert lab.clients["user"].get("/me", headers=lab.headers(token)).json()["roles"] == ["sys_admin"]
