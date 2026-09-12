"""HTTP borné : aucun corps fournisseur, prompt ou secret dans les exceptions."""
import hmac
import json
import math
import threading
import time
import httpx
from fastapi import Header, HTTPException, Request


class DependencyFailure(Exception):
    def __init__(self, code, status=503):
        self.code, self.status = code, status
        super().__init__(code)


def post(url, payload, headers=None, timeout=25, max_bytes=2_000_000):
    try:
        with httpx.Client(timeout=httpx.Timeout(timeout, connect=3), trust_env=False, follow_redirects=False) as client:
            with client.stream("POST", url, json=payload, headers=headers) as response:
                if response.status_code != 200:
                    code = {401: "provider_auth", 403: "dependency_denied", 429: "provider_quota", 404: "provider_missing"}.get(response.status_code, "dependency_http")
                    raise DependencyFailure(code, response.status_code if response.status_code in {403, 429} else 503)
                body = bytearray()
                started = time.monotonic()
                for block in response.iter_bytes():
                    body.extend(block)
                    if len(body) > max_bytes or time.monotonic() - started > timeout:
                        raise DependencyFailure("response_limit")
                return json.loads(body)
    except httpx.TimeoutException:
        raise DependencyFailure("dependency_timeout") from None
    except (httpx.HTTPError, ValueError):
        raise DependencyFailure("dependency_invalid") from None


class Circuit:
    def __init__(self):
        self.lock, self.failures, self.until = threading.Lock(), 0, 0

    def check(self):
        with self.lock:
            if time.monotonic() < self.until:
                raise DependencyFailure("circuit_open")

    def result(self, success):
        with self.lock:
            self.failures = 0 if success else self.failures + 1
            if self.failures >= 3:
                self.until = time.monotonic() + 30


def internal(request: Request, supplied: str | None = Header(default=None, alias="X-Edu-Internal")):
    supplied = supplied or ""
    expected = request.app.state.settings.internal_key_file.read_text().strip()
    if not expected or not hmac.compare_digest(supplied, expected):
        raise HTTPException(403, "Accès interservices requis.")


def headers(request, *, private=False):
    result = {"Authorization": request.headers.get("Authorization", "")}
    if private:
        result["X-Edu-Internal"] = request.app.state.settings.internal_key_file.read_text().strip()
    return result


def safety(request, text, student_id, destination="local"):
    result = post(request.app.state.settings.safety_url + "/analyze", {
        "text": text, "student_id": str(student_id) if student_id else None, "destination": destination}, headers(request), timeout=8)
    if not isinstance(result, dict) or result.get("decision") not in {"allow", "redact", "block"}:
        raise DependencyFailure("safety_invalid")
    clean = result.get("sanitized_text")
    if result["decision"] == "block":
        raise HTTPException(403, "Transmission refusée par la politique de sécurité ou de consentement.")
    if not isinstance(clean, str) or not clean.strip():
        raise DependencyFailure("safety_invalid")
    return clean


def embeddings(settings, texts, *, query=False):
    prefix = "task: search result | query: " if query else "title: Programme scolaire | text: "
    data = post(settings.ollama_url + "/api/embed", {"model": settings.embedding_model,
        "input": [prefix + x for x in texts], "truncate": False, "keep_alive": "5m"}, timeout=25)
    vectors = data.get("embeddings") if isinstance(data, dict) else None
    if not isinstance(vectors, list) or len(vectors) != len(texts):
        raise DependencyFailure("embedding_invalid")
    for vector in vectors:
        if not isinstance(vector, list) or len(vector) != 768 or not all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) for x in vector) or sum(x*x for x in vector) < 1e-12:
            raise DependencyFailure("embedding_dimensions")
    return vectors


def install_errors(app):
    from fastapi.responses import JSONResponse
    @app.exception_handler(DependencyFailure)
    async def unavailable(request, exc):
        return JSONResponse(status_code=exc.status, content={"detail": exc.code})
