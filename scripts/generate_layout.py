"""Génère Compose et Nginx, sans écraser le code des services existants."""
from pathlib import Path
import json
import yaml

root = Path(__file__).resolve().parents[1]
images = json.loads((root / "infra" / "images.lock.json").read_text())

def image(tag):
    return f"{tag}@{images[tag]}"
names = "auth user class curriculum content exercise assessment tutor retrieval speech notification analytics admin safety ai-router".split()
secrets = {name: {"file": f"./secrets/{name}"} for name in ["postgres_password", "redis_password", "db_migrator", *["db_" + name.replace("-", "_") for name in names]]}
secrets.update({name: {"file": f"./secrets/{name}"} for name in ["jwt_private_key", "jwt_public_keys", "pii_keys", "rate_key", "redis_auth", "redis_user", "redis_safety", "redis_curriculum", "redis_content", "redis_exercise", "redis_assessment", "redis_tutor", "redis_retrieval", "redis_ai-router", "redis_class", "redis_analytics", "redis_admin", "redis_speech", "redis_notification", "redis_web"]})
base = {
    "name": "educapilote",
    "services": {
        "postgres": {
            "image": image("pgvector/pgvector:pg17"), "restart": "unless-stopped",
            "environment": {"POSTGRES_DB": "educapilote", "POSTGRES_USER": "postgres", "POSTGRES_PASSWORD_FILE": "/run/secrets/postgres_password", "POSTGRES_INITDB_ARGS": "--auth-host=scram-sha-256 --data-checksums"},
            "command": ["postgres", "-c", "max_connections=100", "-c", "shared_buffers=128MB", "-c", "password_encryption=scram-sha-256", "-c", "log_statement=none", "-c", "log_min_error_statement=panic", "-c", "log_parameter_max_length_on_error=0"],
            "volumes": ["postgres_data:/var/lib/postgresql/data", "./infra/postgres/init.sh:/docker-entrypoint-initdb.d/10-roles.sh:ro"],
            "secrets": [key for key in secrets if key.startswith("db_") or key == "postgres_password"],
            "healthcheck": {"test": ["CMD-SHELL", "pg_isready -U postgres -d educapilote"], "interval": "5s", "timeout": "3s", "retries": 20},
            "networks": ["backend"], "shm_size": "256mb", "mem_limit": "768m", "cpus": 1.5,
            "security_opt": ["no-new-privileges:true"],
        },
        "redis": {
            "image": image("redis:7.4-alpine"), "restart": "unless-stopped", "user": "999:999",
            "entrypoint": ["/bin/sh", "/etc/redis/start.sh"],
            "volumes": ["redis_data:/data", "./infra/redis/redis.conf:/etc/redis/redis.conf:ro", "./infra/redis/start.sh:/etc/redis/start.sh:ro"],
            "secrets": ["redis_password", "redis_auth", "redis_user", "redis_safety", "redis_curriculum", "redis_content", "redis_exercise", "redis_assessment", "redis_tutor", "redis_retrieval", "redis_ai-router", "redis_class", "redis_analytics", "redis_admin", "redis_speech", "redis_notification", "redis_web"], "read_only": True, "tmpfs": ["/tmp:rw,noexec,nosuid,size=4m"],
            "healthcheck": {"test": ["CMD-SHELL", "REDISCLI_AUTH=$$(cat /run/secrets/redis_password) redis-cli ping | grep -q PONG"], "interval": "5s", "timeout": "3s", "retries": 20},
            "networks": ["backend"], "cap_drop": ["ALL"], "security_opt": ["no-new-privileges:true"], "mem_limit": "320m", "cpus": 0.5,
        },
        "migrate": {
            "build": {"context": ".", "dockerfile": "infra/Dockerfile", "target": "migrate"},
            "environment": {"EDU_DB_USER": "edu_migrator", "EDU_DB_PASSWORD_FILE": "/run/secrets/db_migrator"},
            "secrets": ["db_migrator"], "depends_on": {"postgres": {"condition": "service_healthy"}},
            "networks": ["backend"], "read_only": True, "cap_drop": ["ALL"], "security_opt": ["no-new-privileges:true"], "mem_limit": "256m", "cpus": 0.5,
        },
    },
    "volumes": {"postgres_data": {}, "redis_data": {}},
    "networks": {"backend": {"internal": True}, "edge": {}},
    "secrets": secrets,
}
for name in names:
    service = name + "-service"
    role = name.replace("-", "_")
    directory = root / "services" / service / "app"
    directory.mkdir(parents=True, exist_ok=True)
    if not (directory / "main.py").exists():
        (directory / "__init__.py").write_text("", encoding="utf-8")
        (directory / "main.py").write_text(f'from shared.app import create_app\nfrom shared.config import Settings\n\napp = create_app(Settings(service_name="{service}"))\n', encoding="utf-8")
    base["services"][service] = {
        "build": {"context": ".", "dockerfile": "infra/Dockerfile", "target": "service", "args": {"SERVICE_NAME": service}},
        "restart": "unless-stopped", "environment": {"EDU_DB_USER": f"edu_{role}"},
        "secrets": [{"source": f"db_{role}", "target": "db_password"}, "redis_password"],
        "depends_on": {"migrate": {"condition": "service_completed_successfully"}, "redis": {"condition": "service_healthy"}},
        "networks": ["backend"], "read_only": True, "tmpfs": ["/tmp:rw,noexec,nosuid,size=16m"],
        "cap_drop": ["ALL"], "security_opt": ["no-new-privileges:true"], "mem_limit": "192m", "cpus": 0.5,
        "healthcheck": {"test": ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/ready', timeout=8)"], "interval": "30s", "timeout": "10s", "retries": 3, "start_period": "30s"},
    }
    if name in {"auth", "user", "safety", "curriculum", "content", "exercise", "assessment", "tutor", "retrieval", "ai-router", "class", "analytics", "admin", "speech", "notification"}:
        service_config = base["services"][service]
        service_config["environment"].update({"EDU_REDIS_USERNAME": f"edu_{name}", "EDU_JWT_ACTIVE_KID": "${EDU_JWT_ACTIVE_KID:-edu-key-1}"})
        service_config["secrets"] = [{"source": f"db_{role}", "target": "db_password"},
            {"source": f"redis_{name}", "target": "redis_password"}, "jwt_public_keys", "rate_key"]
        if name in {"auth", "user", "safety", "assessment"}:
            service_config["secrets"].append("jwt_private_key" if name == "auth" else "pii_keys")
        service_config["mem_limit"] = "768m" if name == "safety" else "512m"
        service_config["cpus"] = 1.0
        if name == "safety":
            service_config["build"]["target"] = "safety"
secrets["ai_internal_key"] = {"file": "./secrets/ai_internal_key"}
for name in ["tutor", "retrieval", "ai-router"]:
    base["services"][name + "-service"]["secrets"].append("ai_internal_key")
for name in ["retrieval", "ai-router"]:
    base["services"][name + "-service"]["extra_hosts"] = ["ollama-host:${EDU_OLLAMA_HOST_IP:-host-gateway}"]
for name in ["tutor", "retrieval", "ai-router"]:
    base["services"][name + "-service"]["environment"]["EDU_EMBEDDING_MODEL"] = "${EDU_EMBEDDING_MODEL:-educapilote-embeddinggemma:v1}"
base["services"]["ai-router-service"]["environment"].update({
    "EDU_CLOUD_MODEL": "${EDU_CLOUD_MODEL:-gpt-oss:120b-cloud}", "EDU_AI_DAILY_CALLS": "${EDU_AI_DAILY_CALLS:-200}"})
base["services"]["retrieval-service"]["networks"].append("edge")
base["services"]["proxy"] = {
    "image": image("nginx:stable-alpine"), "restart": "unless-stopped", "user": "101:101",
    "entrypoint": ["nginx", "-g", "daemon off;"],
    "ports": ["${EDU_BIND_IP:-127.0.0.1}:${EDU_HTTP_PORT:-18088}:8080"],
    "volumes": ["./infra/nginx/nginx.dev.conf:/etc/nginx/nginx.conf:ro"],
    "networks": ["edge", "backend"], "read_only": True,
    "tmpfs": ["/tmp:rw,noexec,nosuid,size=32m"], "cap_drop": ["ALL"], "security_opt": ["no-new-privileges:true"],
    "mem_limit": "64m", "cpus": 0.5,
    "depends_on": {name + "-service": {"condition": "service_healthy"} for name in names},
    "healthcheck": {"test": ["CMD", "wget", "-q", "-O", "/dev/null", "http://127.0.0.1:8080/health/live"], "interval": "30s", "timeout": "3s", "retries": 3},
}
base["services"]["test"] = {
    "profiles": ["test"], "build": {"context": ".", "dockerfile": "infra/Dockerfile", "target": "test"},
    "environment": {"EDU_TEST_INTEGRATION": "1"},
    "secrets": ["postgres_password", "db_user", "db_auth", "db_safety", "db_content", "db_admin", "db_curriculum", "db_migrator", "db_exercise", "db_assessment", "db_tutor", "db_retrieval", "db_ai_router", "db_class", "db_analytics", "db_speech", "db_notification", "automation_keys", "ai_internal_key",
        "jwt_private_key", "jwt_public_keys", "pii_keys", "rate_key", "redis_auth", "redis_user", "redis_safety", "redis_curriculum", "redis_content", "redis_exercise", "redis_assessment", "redis_tutor", "redis_retrieval", "redis_ai-router", "redis_class", "redis_analytics", "redis_admin", "redis_speech", "redis_notification", "redis_web"],
    "depends_on": {"migrate": {"condition": "service_completed_successfully"}}, "networks": ["backend"],
    "read_only": True, "tmpfs": ["/tmp:rw,noexec,nosuid,size=64m"], "cap_drop": ["ALL"], "security_opt": ["no-new-privileges:true"], "mem_limit": "4096m",
}
secrets["automation_keys"] = {"file": "./secrets/automation_keys"}
base["services"]["notification-service"]["secrets"].append("automation_keys")
base["services"]["speech-service"]["build"]["target"] = "speech"
import copy
worker = copy.deepcopy(base["services"]["notification-service"])
worker["command"] = ["python", "-m", "app.worker"]
worker.pop("healthcheck")
base["services"]["notification-worker"] = worker
base["services"]["web"] = {
    "build": {"context":"./apps/web","dockerfile":"Dockerfile"},
    "restart":"unless-stopped", "environment":{"LOGIN_SCHOOL_ID":"${EDU_LOGIN_SCHOOL_ID:-}","WEB_ORIGINS":"${EDU_WEB_ORIGINS:-http://localhost:18088,http://127.0.0.1:18088}","COOKIE_SECURE":"${EDU_COOKIE_SECURE:-false}","REDIS_PASSWORD_FILE":"/run/secrets/redis_web","HOSTNAME":"0.0.0.0","PORT":"3000"},
    "secrets":["redis_web"], "networks":["backend"],
    "depends_on":{"redis":{"condition":"service_healthy"}},
    "healthcheck":{"test":["CMD","node","-e","fetch('http://127.0.0.1:3000/api/health').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"],"interval":"10s","timeout":"5s","retries":12},
    "read_only":True,"tmpfs":["/tmp:rw,noexec,nosuid,size=64m"],"cap_drop":["ALL"],"security_opt":["no-new-privileges:true"],"mem_limit":"768m","cpus":1.5
}

for service in base["services"].values():
    service["logging"] = {"driver": "json-file", "options": {"max-size": "10m", "max-file": "3"}}
(root / "docker-compose.dev.yml").write_text(yaml.safe_dump(base, sort_keys=False, allow_unicode=True), encoding="utf-8")
nginx = root / "infra" / "nginx"
nginx.mkdir(parents=True, exist_ok=True)
header = '''worker_processes auto;
pid /tmp/nginx.pid;
error_log /dev/stderr warn;
events { worker_connections 1024; }
http {
  access_log off;
  server_tokens off;
  client_body_temp_path /tmp/client;
  proxy_temp_path /tmp/proxy;
  fastcgi_temp_path /tmp/fastcgi;
  uwsgi_temp_path /tmp/uwsgi;
  scgi_temp_path /tmp/scgi;
  resolver 127.0.0.11 valid=10s ipv6=off;
  limit_req_zone $binary_remote_addr zone=requests:10m rate=10r/s;
  server {
    listen 8080;
    client_max_body_size 1m;
    add_header X-Content-Type-Options nosniff always;
    add_header Referrer-Policy no-referrer always;
    add_header X-Frame-Options DENY always;
    location = /health/live { default_type application/json; return 200 '{"status":"ok"}'; }
'''
locations = ""
for name in names:
    service = name + "-service"
    locations += f'''    location /services/{service}/ {{
      limit_req zone=requests burst=30 nodelay;
      set $upstream "{service}:8000";
      rewrite ^/services/{service}/(.*)$ /$1 break;
      proxy_pass http://$upstream;
      proxy_set_header Host $host;
      proxy_set_header X-Forwarded-Proto $scheme;
      proxy_set_header X-Forwarded-For $remote_addr;
      proxy_connect_timeout 3s;
      proxy_read_timeout 120s;
    }}
'''
    locations += f'    location = /services/{service}/metrics {{ return 404; }}\n'
tail = """    location / {
      set $web "web:3000";
      proxy_pass http://$web;
      proxy_set_header Host $http_host;
      proxy_set_header X-Forwarded-Proto $scheme;
      proxy_read_timeout 90s;
    }
  }
}
"""
(nginx / "nginx.dev.conf").write_text(header + locations + tail, encoding="utf-8")
prod_header = header.replace("listen 8080;", '''listen 8080;
    listen 8443 ssl;
    ssl_certificate /run/tls/fullchain.pem;
    ssl_certificate_key /run/tls/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_session_tickets off;
    add_header Strict-Transport-Security "max-age=31536000" always;''')
# Le port 8080 reste interne pour le healthcheck ; seul 8443 est publié en production.
(nginx / "nginx.prod.conf").write_text(prod_header + locations + tail, encoding="utf-8")
