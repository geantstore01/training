import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from prometheus_client import generate_latest
from shared.observability import install, Telemetry
from scripts.sentry_forwarder import before_send, safe_event


def test_request_telemetry_contains_no_identity(tmp_path, monkeypatch):
    monkeypatch.setenv("EDU_TELEMETRY_LOG_DIR",str(tmp_path))
    app = FastAPI()
    install(app,"user-service")
    @app.get("/students/{student_id}")
    def route(student_id: str): return {"ok":True}
    @app.get("/fail")
    def fail(): raise ValueError("PII Alice alice@example.org secret-token")
    with TestClient(app,raise_server_exceptions=False) as client:
        r = client.get("/students/alice@example.org?secret=token",headers={"Authorization":"Bearer secret-token"})
        assert r.status_code == 200
        assert len(r.headers["x-request-id"]) == 32
        client.get("/unknown-Alice")
        assert client.get("/fail").status_code == 500
        metrics = client.get("/metrics").text
    app.state.telemetry.close()
    logs = next(tmp_path.glob("user-service.*.jsonl")).read_text()
    for secret in ("Alice","alice@example.org","secret-token","unknown-Alice"):
        assert secret not in metrics + logs
    assert '/students/{student_id}' in metrics
    assert 'status="500"' in metrics
    assert any(json.loads(row)["status"] == 500 for row in logs.splitlines())


def test_ai_cost_is_explicit_estimate(monkeypatch):
    monkeypatch.setenv("EDU_AI_INPUT_EUR_PER_MILLION","2")
    monkeypatch.setenv("EDU_AI_OUTPUT_EUR_PER_MILLION","6")
    telemetry = Telemetry("ai-router-service")
    telemetry.ai_result("completed",1,1000,500)
    metrics = generate_latest(telemetry.registry).decode()
    assert 'edu_ai_estimated_cost_eur_total 0.005' in metrics
    assert 'edu_ai_pricing_configured 1.0' in metrics


def test_no_price_does_not_claim_free_service(monkeypatch):
    monkeypatch.delenv("EDU_AI_INPUT_EUR_PER_MILLION",raising=False)
    monkeypatch.delenv("EDU_AI_OUTPUT_EUR_PER_MILLION",raising=False)
    telemetry = Telemetry("ai-router-service")
    assert telemetry.rates is None
    assert 'edu_ai_pricing_configured 0.0' in generate_latest(telemetry.registry).decode()


@pytest.mark.parametrize("value",["nan","inf","-1"])
def test_invalid_prices_rejected(monkeypatch,value):
    monkeypatch.setenv("EDU_AI_INPUT_EUR_PER_MILLION",value)
    monkeypatch.setenv("EDU_AI_OUTPUT_EUR_PER_MILLION","1")
    with pytest.raises(ValueError): Telemetry("ai-router-service")


def test_sentry_allowlist_discards_sensitive_context():
    event = safe_event({"status":503,"service":"tutor-service","body":"PII","route":"/alice","headers":{"cookie":"secret"}})
    event.update(request={"data":"secret"},user={"email":"alice@example.org"},extra={"pii":"yes"},breadcrumbs=["secret"])
    filtered = before_send(event,{})
    assert set(filtered) == {"message","level","tags","fingerprint"}
    assert "alice" not in json.dumps(filtered)
    assert before_send({"tags":{"service":"arbitrary-pii","status":"500"}}, {}) is None
    assert safe_event({"service":"tutor-service","status":200}) is None


def test_sentry_sdk_transport_receives_only_safe_payload():
    import sentry_sdk
    from sentry_sdk.transport import Transport
    envelopes = []
    class MemoryTransport(Transport):
        def capture_envelope(self, envelope): envelopes.append(envelope)
    with sentry_sdk.init(dsn="https://public@example.invalid/1", transport=MemoryTransport,
            default_integrations=False, auto_enabling_integrations=False, send_default_pii=False,
            before_send=before_send):
        event = safe_event({"service":"user-service","status":500})
        event.update(user={"email":"PII@example.org"},request={"headers":{"Cookie":"secret"}},extra={"body":"PII"})
        sentry_sdk.capture_event(event)
        sentry_sdk.flush()
    assert len(envelopes) == 1
    serialized = envelopes[0].serialize().decode()
    assert "PII" not in serialized and "secret" not in serialized and "Cookie" not in serialized
    assert "Application HTTP 5xx" in serialized


def test_logging_failure_does_not_break_requests(tmp_path,monkeypatch):
    path = tmp_path / "not-a-directory"
    path.write_text("fixture")
    monkeypatch.setenv("EDU_TELEMETRY_LOG_DIR",str(path))
    app = FastAPI()
    install(app,"user-service")
    @app.get("/ok")
    def route(): return {"ok":True}
    with TestClient(app) as client:
        assert client.get("/ok").status_code == 200


def test_log_retention_only_removes_expired_technical_files(tmp_path):
    from datetime import datetime, timezone
    from scripts.host_metrics import purge_technical_logs
    directory = tmp_path / "user-service"
    directory.mkdir()
    old = directory / "user-service.20260903.jsonl.1"
    retained = directory / "user-service.20260904.jsonl"
    unrelated = directory / "operator-notes.jsonl"
    for path in (old,retained,unrelated): path.write_text("fixture")
    purge_technical_logs(tmp_path,datetime(2026,9,10,tzinfo=timezone.utc))
    assert not old.exists()
    assert retained.exists() and unrelated.exists()


def test_prod_boundaries():
    import yaml
    root = Path(__file__).resolve().parents[1]
    if not (root/"docker-compose.prod.yml").exists(): pytest.skip("Compose not copied into runtime test image")
    compose = yaml.safe_load((root/"docker-compose.prod.yml").read_text(encoding="utf-8"))
    assert len([name for name in compose["services"] if name.endswith("-service")]) == 15
    for name,service in compose["services"].items():
        if name != "traefik":
            for port in service.get("ports",[]):
                assert "127.0.0.1:" in port or name == "proxy"
        assert not any("docker.sock" in v for v in service.get("volumes",[]))
    assert compose["services"]["web"]["environment"]["COOKIE_SECURE"] == "true"
    assert "local-ollama" in compose["services"]["ollama"]["profiles"]
