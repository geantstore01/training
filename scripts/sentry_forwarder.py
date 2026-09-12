"""Forward only safe technical 5xx events. No automatic Sentry integrations."""
import json
import os
from pathlib import Path
import re
import time
import sentry_sdk

SERVICES = {n + "-service" for n in "auth user class curriculum content exercise assessment tutor retrieval speech notification analytics admin safety ai-router".split()}


def safe_event(row):
    if row.get("service") not in SERVICES or type(row.get("status")) is not int or not 500 <= row["status"] <= 599:
        return None
    # Deliberately omit even route templates and correlation IDs in third-party tracking.
    return {"message": "Application HTTP 5xx", "level": "error", "tags": {"service": row["service"], "status": str(row["status"])},
        "fingerprint": ["http-5xx", row["service"], str(row["status"])]}


def before_send(event, hint):
    tags = event.get("tags", {})
    service, status = tags.get("service"), tags.get("status", "")
    if service not in SERVICES or not re.fullmatch(r"5[0-9]{2}", status):
        return None
    result = safe_event({"service": service, "status": int(status)})
    if re.fullmatch(r"[0-9a-f]{32}", event.get("event_id", "")):
        result["event_id"] = event["event_id"]
    return result


def main():
    dsn = Path("/run/secrets/sentry_dsn").read_text().strip()
    sentry_sdk.init(dsn=dsn or None, default_integrations=False, auto_enabling_integrations=False,
        send_default_pii=False, include_local_variables=False, include_source_context=False,
        max_breadcrumbs=0, traces_sample_rate=0, profiles_sample_rate=0, auto_session_tracking=False,
        send_client_reports=False, before_send=before_send)
    state = Path("/state/offsets.json")
    offsets = json.loads(state.read_text()) if state.exists() else {}
    print("Sentry forwarding enabled" if dsn else "Sentry disabled: DSN not configured", flush=True)
    while True:
        for path in Path("/logs").rglob("*-service.*.jsonl*"):
            if not path.is_file():
                continue
            stat = path.stat()
            key = str(stat.st_ino)
            position = offsets.get(key, 0)
            if position > stat.st_size:
                position = 0
            with path.open("rb") as stream:
                stream.seek(position)
                for _ in range(1000):
                    line = stream.readline(65536)
                    if not line or not line.endswith(b"\n"):
                        break
                    position = stream.tell()
                    try:
                        row = json.loads(line)
                        event = safe_event(row) if isinstance(row, dict) else None
                        if event and dsn:
                            sentry_sdk.capture_event(event)
                    except (ValueError, TypeError):
                        pass
            offsets[key] = position
        present = {str(p.stat().st_ino) for p in Path("/logs").rglob("*-service.*.jsonl*") if p.is_file()}
        offsets = {key: value for key, value in offsets.items() if key in present}
        temp = state.with_suffix(".tmp")
        temp.write_text(json.dumps(offsets))
        temp.replace(state)
        time.sleep(2)


if __name__ == "__main__":
    main()
