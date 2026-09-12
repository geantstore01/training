"""Reproducible standalone production Compose and private observability overlay."""
import copy
import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
NAMES = [n + "-service" for n in "auth user class curriculum content exercise assessment tutor retrieval speech notification analytics admin safety ai-router".split()]


def generate():
    locks = json.loads((ROOT / "infra/production-images.lock.json").read_text(encoding="utf-8"))
    def image(tag):
        return tag + "@" + locks[tag]
    def daemon(tag, memory, **kwargs):
        return dict(image=image(tag), restart="unless-stopped", networks=["monitoring"],
            read_only=True, cap_drop=["ALL"], security_opt=["no-new-privileges:true"],
            mem_limit=memory, cpus=1.0, logging={"driver":"json-file","options":{"max-size":"10m","max-file":"3"}}, **kwargs)
    overlay = {"name":"educapilote", "services":{}, "volumes":{
        n:{} for n in ["prometheus_data","grafana_data","loki_data","alloy_data","sentry_state"]},
        "networks":{"monitoring":{"internal":True}, "telemetry_egress":{}, "operations_access":{}},
        "secrets":{"grafana_password":{"file":"./secrets/grafana_password"},"sentry_dsn":{"file":"./secrets/sentry_dsn"}}}
    services = overlay["services"]
    for name in NAMES:
        services[name] = {"environment":{"EDU_TELEMETRY_LOG_DIR":"/var/log/edu"},
            "volumes":[f"./runtime/telemetry/{name}:/var/log/edu"]}
    services["ai-router-service"]["environment"].update({
        "EDU_AI_INPUT_EUR_PER_MILLION":"${EDU_AI_INPUT_EUR_PER_MILLION:-}",
        "EDU_AI_OUTPUT_EUR_PER_MILLION":"${EDU_AI_OUTPUT_EUR_PER_MILLION:-}"})
    services["prometheus"] = daemon("prom/prometheus:v3.14.0", "512m", user="65534:65534",
        command=["--config.file=/etc/prometheus/prometheus.yml","--storage.tsdb.path=/prometheus",
            "--storage.tsdb.retention.time=15d","--storage.tsdb.retention.size=2GB"],
        volumes=["./infra/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro",
            "./infra/monitoring/alerts.yml:/etc/prometheus/alerts.yml:ro","prometheus_data:/prometheus"],
        ports=["127.0.0.1:19090:9090"])
    services["prometheus"]["networks"].append("backend")
    services["prometheus"]["networks"].append("operations_access")
    services["grafana"] = daemon("grafana/grafana:13.2.1", "512m", user="472:472",
        ports=["127.0.0.1:13000:3000"], tmpfs=["/tmp:rw,noexec,nosuid,size=32m"],
        environment={"GF_SECURITY_ADMIN_PASSWORD__FILE":"/run/secrets/grafana_password",
            "GF_USERS_ALLOW_SIGN_UP":"false", "GF_AUTH_ANONYMOUS_ENABLED":"false", "GF_AUTH_DISABLE_LOGIN_FORM":"false",
            "GF_ANALYTICS_REPORTING_ENABLED":"false", "GF_ANALYTICS_CHECK_FOR_UPDATES":"false",
            "GF_ANALYTICS_CHECK_FOR_PLUGIN_UPDATES":"false", "GF_SECURITY_COOKIE_SAMESITE":"strict",
            "GF_LOG_LEVEL":"warn"}, secrets=["grafana_password"],
        volumes=["grafana_data:/var/lib/grafana","./infra/monitoring/grafana:/etc/grafana/provisioning:ro",
            "./infra/monitoring/dashboards:/var/lib/edu-dashboards:ro"])
    services["grafana"]["networks"].append("operations_access")
    services["loki"] = daemon("grafana/loki:3.7.7", "384m", user="10001:10001",
        command=["-config.file=/etc/loki/config.yml"], volumes=["./infra/monitoring/loki.yml:/etc/loki/config.yml:ro","loki_data:/loki"])
    services["alloy"] = daemon("grafana/alloy:v1.19.2", "256m", user="10001:10001",
        command=["run","--server.http.listen-addr=0.0.0.0:12345","--storage.path=/data","/etc/alloy/config.alloy"],
        volumes=["./infra/monitoring/config.alloy:/etc/alloy/config.alloy:ro", "./runtime/telemetry:/logs:ro",
            {"type":"volume","source":"alloy_data","target":"/data","volume":{"nocopy":True}}])
    services["node-exporter"] = daemon("prom/node-exporter:v1.12.1", "128m", user="65534:65534", pid="host",
        command=["--path.procfs=/host/proc","--path.sysfs=/host/sys","--path.rootfs=/rootfs",
            "--collector.textfile.directory=/textfile","--collector.filesystem.mount-points-exclude=^/(dev|proc|sys|var/lib/docker/.+)($$|/)"],
        volumes=["/proc:/host/proc:ro","/sys:/host/sys:ro","/:/rootfs:ro,rslave","./runtime/metrics:/textfile:ro"])
    services["sentry-forwarder"] = {
        "build":{"context":".","dockerfile":"infra/Dockerfile","target":"base"},
        "command":["python","-m","scripts.sentry_forwarder"], "restart":"unless-stopped",
        "networks":["telemetry_egress"], "secrets":["sentry_dsn"],
        "volumes":["./runtime/telemetry:/logs:ro","sentry_state:/state"], "read_only":True,
        "cap_drop":["ALL"],"security_opt":["no-new-privileges:true"],"mem_limit":"128m", "cpus":0.25,
        "logging":{"driver":"json-file","options":{"max-size":"5m","max-file":"2"}}}
    # One-shot ownership initialization only touches these five named volumes.
    services["monitoring-init"] = {
        "image":image("grafana/alloy:v1.19.2"), "user":"0:0", "entrypoint":["/bin/sh","-ec"],
        "command":["chown 65534:65534 /prometheus; chown 472:472 /grafana; chown 10001:10001 /loki /alloy /state"],
        "volumes":["prometheus_data:/prometheus","grafana_data:/grafana","loki_data:/loki","alloy_data:/alloy","sentry_state:/state"],
        "network_mode":"none", "read_only":True,"cap_drop":["ALL"],"cap_add":["CHOWN"],
        "security_opt":["no-new-privileges:true"], "mem_limit":"64m"}
    for name in ("prometheus","grafana","loki","alloy","sentry-forwarder"):
        services[name]["depends_on"] = {"monitoring-init":{"condition":"service_completed_successfully"}}
    (ROOT / "docker-compose.observability.yml").write_text(yaml.safe_dump(overlay, sort_keys=False), encoding="utf-8")
    prod = yaml.safe_load((ROOT / "docker-compose.dev.yml").read_text(encoding="utf-8"))
    for key in ("volumes","networks","secrets"):
        prod[key].update(overlay[key])
    for name, value in services.items():
        if name in prod["services"]:
            for key, entry in value.items():
                if isinstance(entry, dict): prod["services"][name].setdefault(key,{}).update(entry)
                else: prod["services"][name].setdefault(key,[]).extend(entry)
        else: prod["services"][name] = copy.deepcopy(value)
    prod["services"]["web"]["environment"].update({"COOKIE_SECURE":"true", "WEB_ORIGINS":"https://${EDU_DOMAIN:?Set EDU_DOMAIN}"})
    prod["services"]["proxy"]["ports"] = ["127.0.0.1:${EDU_HTTP_PORT:-18088}:8080"]
    prod["services"]["traefik"] = daemon("traefik:v3.7.13", "256m", user="10001:10001",
        ports=["${EDU_HTTPS_BIND_IP:-0.0.0.0}:${EDU_HTTPS_PORT:-443}:8443"],
        environment={"EDU_DOMAIN":"${EDU_DOMAIN:?Set EDU_DOMAIN}"},
        command=["--entrypoints.websecure.address=:8443","--entrypoints.health.address=:8082",
            "--ping=true","--ping.entrypoint=health", "--api.dashboard=false",
            "--providers.file.filename=/etc/traefik/dynamic.yml",
            "--certificatesresolvers.le.acme.email=${EDU_ACME_EMAIL:?Set EDU_ACME_EMAIL}",
            "--certificatesresolvers.le.acme.storage=/acme/acme.json", "--certificatesresolvers.le.acme.tlschallenge=true",
            "--certificatesresolvers.le.acme.caserver=${EDU_ACME_CA:-https://acme-staging-v02.api.letsencrypt.org/directory}",
            "--metrics.prometheus=true", "--metrics.prometheus.entrypoint=health", "--log.level=WARN"],
        volumes=["./infra/traefik/dynamic.yml:/etc/traefik/dynamic.yml:ro","./runtime/acme:/acme"],
        healthcheck={"test":["CMD","traefik","healthcheck","--ping","--ping.entrypoint=health","--entrypoints.health.address=:8082"],"interval":"15s","timeout":"5s","retries":5})
    prod["services"]["traefik"]["networks"] = ["backend","monitoring","edge"]
    prom = yaml.safe_load((ROOT / "infra/monitoring/prometheus.yml").read_text(encoding="utf-8"))
    prom["scrape_configs"].append({"job_name":"traefik","static_configs":[{"targets":["traefik:8082"]}]})
    (ROOT / "infra/monitoring/prometheus.prod.yml").write_text(yaml.safe_dump(prom,sort_keys=False),encoding="utf-8")
    prod["services"]["prometheus"]["volumes"][0] = "./infra/monitoring/prometheus.prod.yml:/etc/prometheus/prometheus.yml:ro"
    prod["services"]["ollama"] = daemon("ollama/ollama:0.34.0", "8g", profiles=["local-ollama"],
        environment={"OLLAMA_HOST":"0.0.0.0:11434","OLLAMA_NUM_PARALLEL":"1","OLLAMA_MAX_LOADED_MODELS":"1","OLLAMA_KEEP_ALIVE":"5m"},
        volumes=["ollama_data:/root/.ollama"], tmpfs=["/tmp:rw,nosuid,size=256m"],
        deploy={"resources":{"reservations":{"devices":[{"driver":"nvidia","device_ids":["${EDU_GPU_ID:-0}"],"capabilities":["gpu"]}]}}})
    prod["services"]["ollama"]["networks"] = ["backend","edge"]
    prod["services"]["ollama"]["cpus"] = 4.0
    prod["services"]["ollama"]["healthcheck"] = {"test":["CMD","ollama","list"],"interval":"15s","timeout":"10s","retries":5,"start_period":"30s"}
    prod["volumes"]["ollama_data"] = {}
    for name in ("ai-router-service","retrieval-service"):
        prod["services"][name]["environment"]["EDU_OLLAMA_URL"] = "${EDU_OLLAMA_URL:-http://ollama-host:11434}"
    (ROOT / "docker-compose.prod.yml").write_text("# Standalone; generated by scripts/generate_production.py. Same persistent project as dev.\n" + yaml.safe_dump(prod,sort_keys=False,allow_unicode=True),encoding="utf-8")


if __name__ == "__main__":
    generate()
