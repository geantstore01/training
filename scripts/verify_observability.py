"""Run on the VPS after deployment. No production account or cloud call needed."""
import base64
import json
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request


def fetch(url, headers=None):
    with urllib.request.urlopen(urllib.request.Request(url,headers=headers or {}),timeout=8) as response:
        return json.load(response)


def query(expression):
    result = fetch("http://127.0.0.1:19090/api/v1/query?" + urllib.parse.urlencode({"query":expression}))
    assert result["status"] == "success"
    return result["data"]["result"]


def main():
    targets = fetch("http://127.0.0.1:19090/api/v1/targets")["data"]["activeTargets"]
    app_targets = [t for t in targets if t["labels"].get("job") == "educapilote"]
    assert len(app_targets) == 15 and all(t["health"] == "up" for t in app_targets)
    assert all(t["health"] == "up" for t in targets), "Infrastructure scrape failed"
    assert len(query('edu_dependency_up{dependency="postgres"} == 1')) == 15
    assert len(query('edu_dependency_up{dependency="redis"} == 1')) == 15
    assert query("edu_gpu_collection_success == 1")
    assert query("time() - edu_backup_last_success_timestamp_seconds < 93600")
    for service in ("auth", "tutor", "user"):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:18088/services/{service}-service/metrics",timeout=5)
            raise AssertionError("Metrics exposed through proxy")
        except urllib.error.HTTPError as error:
            assert error.code == 404
    # A synthetic unmatched route exercises the actual sanitized log pipeline.
    try:
        urllib.request.urlopen("http://127.0.0.1:18088/services/user-service/observability-probe",timeout=5)
    except urllib.error.HTTPError as error:
        assert error.code == 404
    secret = (Path(__file__).resolve().parents[1]/"secrets/grafana_password").read_text().strip()
    headers = {"Authorization":"Basic " + base64.b64encode(("admin:"+secret).encode()).decode()}
    dashboard = fetch("http://127.0.0.1:13000/api/dashboards/uid/educapilote-ops",headers)
    assert len(dashboard["dashboard"]["panels"]) >= 12
    for _ in range(15):
        params = urllib.parse.urlencode({"query":'{job="educapilote",service="user-service"}',"limit":10})
        result = fetch("http://127.0.0.1:13000/api/datasources/proxy/uid/loki/loki/api/v1/query_range?"+params,headers)
        if result["data"]["result"]: break
        time.sleep(2)
    assert result["data"]["result"], "No actual logs ingested by Loki"
    for stream in result["data"]["result"]:
        for _,line in stream["values"]:
            row = json.loads(line)
            assert set(row) == {"event","service","route","method","status","duration_ms","request_id"}
    print("PASS: 15 API targets, dependencies, GPU, backup, private metrics, Grafana dashboard and actual Loki ingestion.")


if __name__ == "__main__": main()
