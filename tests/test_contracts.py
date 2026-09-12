from uuid import uuid4
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import configure_mappers
from sqlalchemy.schema import CreateTable

from shared.app import create_app
from shared.config import Settings
from shared.db.models import Base
from shared.db.session import tenant_session
from shared.dto import HealthResponse


def test_all_requested_tables_and_valid_mappers():
    expected = set("users guardians students teachers schools classes enrollments subjects curriculum_levels competencies competency_prerequisites lessons lesson_versions exercises exercise_versions exercise_attempts answers hints mastery_records learning_sessions spaced_repetition_items ai_interactions safety_events content_sources content_reviews audit_logs consent_records".split())
    assert expected <= Base.metadata.tables.keys()
    configure_mappers()
    for table in Base.metadata.sorted_tables:
        assert "CREATE TABLE" in str(CreateTable(table).compile(dialect=postgresql.dialect()))
        names = [c.name for c in table.constraints if c.name]
        assert len(names) == len(set(names)), table.name


def test_every_scoped_reference_includes_tenant():
    for table in Base.metadata.tables.values():
        for fk in table.foreign_key_constraints:
            target = fk.referred_table
            if "tenant_id" in target.c:
                if table.name == "job_dispatch":
                    assert fk.column_keys == ["school_id", "job_id"]
                    assert [x.target_fullname for x in fk.elements] == ["background_jobs.tenant_id", "background_jobs.id"]
                    continue
                assert "tenant_id" in fk.column_keys, f"{table.name}: {fk}"


def test_no_raw_child_chat_in_telemetry():
    forbidden = {"prompt", "response", "message", "email", "ip_address", "date_of_birth"}
    for name in ["ai_interactions", "safety_events", "audit_logs"]:
        assert not forbidden.intersection(Base.metadata.tables[name].c.keys())


def test_strict_dto():
    with pytest.raises(ValidationError):
        HealthResponse(status="ok", service="auth-service", secret="leak")


def test_live_without_dependencies():
    # Pas de lifespan : ce test vérifie la sonde live, indépendante du réseau.
    client = TestClient(create_app(Settings(service_name="user-service")))
    assert client.get("/health/live").json() == {"status": "ok", "service": "user-service", "module": "infrastructure"}
    schema = client.get("/openapi.json").json()
    assert set(schema["paths"]) == {"/health/live", "/health/ready"}
    assert "503" in schema["paths"]["/health/ready"]["get"]["responses"]


@pytest.mark.parametrize("postgres_ok,redis_ok", [(True, True), (False, True), (True, False), (False, False)])
def test_readiness_checks_both_dependencies(postgres_ok, redis_ok):
    app = create_app()
    engine, cache = MagicMock(), MagicMock()
    app.state.engine, app.state.cache = engine, cache
    engine.connect.return_value.__enter__.return_value.execute.return_value.scalar_one.return_value = 1
    if not postgres_ok:
        engine.connect.side_effect = ConnectionError("sensitive database credential")
    cache.ping.return_value = True
    if not redis_ok:
        cache.ping.side_effect = ConnectionError("sensitive cache credential")
    response = TestClient(app).get("/health/ready")
    assert response.status_code == (200 if postgres_ok and redis_ok else 503)
    assert response.json()["postgres"] is postgres_ok
    assert response.json()["redis"] is redis_ok
    assert "sensitive" not in response.text


def test_invalid_tenant_rejected_before_database_access():
    engine = MagicMock()
    with pytest.raises(ValueError):
        with tenant_session(engine, "not-a-uuid"):
            raise AssertionError("unreachable")
    engine.connect.assert_not_called()
