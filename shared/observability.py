"""Telemetry with bounded labels. Never collect request bodies, headers or raw paths."""
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import time
from uuid import uuid4
from datetime import datetime, timezone

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest
from starlette.responses import Response


class DailyBoundedLog(logging.Handler):
    """One day per filename; size rotation within the day; host timer purges after 7 days."""
    def __init__(self, directory, service):
        super().__init__()
        self.directory, self.service, self.day, self.target = Path(directory), service, None, None

    def emit(self, record):
        day = datetime.now(timezone.utc).strftime("%Y%m%d")
        try:
            if self.day != day:
                if self.target: self.target.close()
                self.target = RotatingFileHandler(self.directory / f"{self.service}.{day}.jsonl",
                    maxBytes=5_000_000, backupCount=2, encoding="utf-8")
                self.target.setFormatter(logging.Formatter("%(message)s"))
                self.day = day
            self.target.emit(record)
        except OSError:
            # Technical logging is best effort and must not break a submitted answer.
            pass

    def close(self):
        if self.target: self.target.close()
        super().close()


class Telemetry:
    def __init__(self, service):
        self.service = service
        self.registry = CollectorRegistry()
        self.dependencies = Gauge("edu_dependency_up", "Last readiness result", ["dependency"], registry=self.registry)
        self.requests = Counter("edu_http_requests_total", "Completed HTTP requests", ["route", "method", "status"], registry=self.registry)
        self.latency = Histogram("edu_http_duration_seconds", "HTTP duration", ["route", "method"],
            buckets=(.01, .05, .1, .25, .5, 1, 2, 5, 10, 30, 60, 120), registry=self.registry)
        self.ai_calls = Counter("edu_ai_calls_total", "Provider calls", ["outcome"], registry=self.registry)
        self.ai_latency = Histogram("edu_ai_duration_seconds", "Cloud plan latency", registry=self.registry,
            buckets=(.1, .5, 1, 2, 5, 10, 20, 30, 60))
        self.tokens = Counter("edu_ai_tokens_total", "Reported provider tokens", ["direction"], registry=self.registry)
        self.cost = Counter("edu_ai_estimated_cost_eur_total", "Estimate only; excludes subscription fees", registry=self.registry)
        self.pricing = Gauge("edu_ai_pricing_configured", "1 when both token prices are configured", registry=self.registry)
        self.rates = None
        import math
        values = [os.getenv("EDU_AI_INPUT_EUR_PER_MILLION"), os.getenv("EDU_AI_OUTPUT_EUR_PER_MILLION")]
        if any(values) and not all(values):
            raise ValueError("Both AI prices are required")
        if all(x is not None and x != "" for x in values):
            rates = tuple(float(x) for x in values)
            if not all(math.isfinite(x) and x >= 0 for x in rates):
                raise ValueError("Invalid AI prices")
            self.rates = rates
        self.pricing.set(int(self.rates is not None))
        self.logger = logging.Logger("edu.safe." + service)
        directory = os.getenv("EDU_TELEMETRY_LOG_DIR")
        if directory:
            handler = DailyBoundedLog(directory, service)
            self.logger.addHandler(handler)
        else:
            self.logger.addHandler(logging.NullHandler())

    def ai_result(self, outcome, duration, input_tokens, output_tokens):
        self.ai_calls.labels(outcome if outcome in {"completed", "failed"} else "failed").inc()
        self.ai_latency.observe(max(0, duration))
        values = [x if type(x) is int and 0 <= x <= 100000 else 0 for x in (input_tokens, output_tokens)]
        for direction, value in zip(("input", "output"), values):
            self.tokens.labels(direction).inc(value)
        if self.rates is not None:
            self.cost.inc(sum(x * rate for x, rate in zip(values, self.rates)) / 1_000_000)

    def close(self):
        for handler in self.logger.handlers:
            handler.close()


class TelemetryMiddleware:
    def __init__(self, app, telemetry, routes):
        self.app, self.telemetry, self.routes = app, telemetry, routes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        started, status = time.monotonic(), 500
        request_id = uuid4().hex
        async def tracked_send(message):
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                message = dict(message)
                message["headers"] = list(message.get("headers", [])) + [(b"x-request-id", request_id.encode())]
            await send(message)
        try:
            await self.app(scope, receive, tracked_send)
        finally:
            route = scope.get("route")
            # Only route templates registered by this application are eligible.
            path = getattr(route, "path", "unmatched") if route in self.routes else "unmatched"
            if path != "/metrics":
                method = scope.get("method")
                method = method if method in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"} else "OTHER"
                duration = time.monotonic() - started
                self.telemetry.requests.labels(path, method, str(status)).inc()
                self.telemetry.latency.labels(path, method).observe(duration)
                if not path.startswith("/health/"):
                    self.telemetry.logger.info(json.dumps({"event": "http_request", "service": self.telemetry.service,
                        "route": path, "method": method, "status": status, "duration_ms": round(duration * 1000),
                        "request_id": request_id}, separators=(",", ":")))


def install(app, service):
    telemetry = Telemetry(service)
    app.state.telemetry = telemetry
    app.add_middleware(TelemetryMiddleware, telemetry=telemetry, routes=app.router.routes)
    async def metrics():
        return Response(generate_latest(telemetry.registry), media_type="text/plain; version=0.0.4; charset=utf-8")
    app.add_api_route("/metrics", metrics, include_in_schema=False)
