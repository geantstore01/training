FROM python:3.11-slim-bookworm@sha256:528257d48c1da0dcecc2e725d1ae34498d60c965f1241e39cd6a85a8859bdf84 AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock
RUN groupadd -g 10001 edu && useradd -u 10001 -g edu -M -s /usr/sbin/nologin edu
USER 10001:10001
EXPOSE 8000

FROM runtime AS nlp_runtime
USER root
COPY requirements-safety.lock ./
RUN pip install --no-cache-dir -r requirements-safety.lock
USER 10001:10001

FROM runtime AS base
COPY shared ./shared
COPY migrations ./migrations
COPY alembic.ini ./
COPY scripts ./scripts

FROM base AS service
ARG SERVICE_NAME
COPY services/${SERVICE_NAME}/app ./app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header", "--no-access-log"]

FROM base AS migrate
CMD ["alembic", "upgrade", "head"]

FROM nlp_runtime AS ner
COPY shared ./shared
COPY migrations ./migrations
COPY alembic.ini ./
COPY scripts ./scripts

FROM ner AS safety
COPY services/safety-service/app ./app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header", "--no-access-log"]

FROM ner AS test
USER root
COPY requirements-test.lock ./
RUN pip install --no-cache-dir -r requirements-test.lock
COPY tests ./tests
COPY workflows ./workflows
COPY services ./services
COPY pyproject.toml ./
COPY docker-compose.prod.yml ./
USER 10001:10001
CMD ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider"]

FROM base AS speech
USER root
RUN apt-get update && apt-get install -y --no-install-recommends espeak-ng && rm -rf /var/lib/apt/lists/*
USER 10001:10001
COPY services/speech-service/app ./app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header", "--no-access-log"]
