from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from redis import Redis
from sqlalchemy import create_engine, text

from shared.config import Settings
from shared.dto import HealthResponse, ReadinessResponse


def create_app(settings: Settings | None = None, initialize=None) -> FastAPI:
    config = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = create_engine(config.database_url(), pool_pre_ping=True,
            pool_size=config.db_pool_size, max_overflow=1,
            connect_args={"connect_timeout": 3, "options": "-c statement_timeout=5000 -c idle_in_transaction_session_timeout=10000"})
        cache = Redis(host=config.redis_host, username=config.redis_username, db=config.redis_db, password=config.redis_password_file.read_text().strip(),
            socket_connect_timeout=3, socket_timeout=3)
        app.state.engine = engine
        app.state.cache = cache
        try:
            if initialize is not None:
                initialize(app)
            yield
        finally:
            cache.close()
            engine.dispose()
            app.state.telemetry.close()

    app = FastAPI(title=f"ÉDUCAPILOTE — {config.service_name}", version="0.1.0",
        description="Module 1 : infrastructure uniquement. Aucun endpoint métier simulé.", lifespan=lifespan,
        root_path=f"/services/{config.service_name}",
        servers=[{"url": f"/services/{config.service_name}"}])
    app.state.settings = config
    from shared.observability import install
    install(app, config.service_name)

    @app.get("/health/live", response_model=HealthResponse, tags=["infrastructure"])
    def live():
        return HealthResponse(status="ok", service=config.service_name)

    @app.get("/health/ready", response_model=ReadinessResponse,
        responses={503: {"model": ReadinessResponse, "description": "Dépendance indisponible"}}, tags=["infrastructure"])
    def ready(response: Response):
        postgres = redis = False
        try:
            with app.state.engine.connect() as connection:
                postgres = connection.execute(text("SELECT 1")).scalar_one() == 1
        except Exception:
            # Aucun détail de connexion ou secret dans la réponse publique.
            postgres = False
        try:
            redis = bool(app.state.cache.ping())
        except Exception:
            redis = False
        healthy = postgres and redis
        app.state.telemetry.dependencies.labels("postgres").set(int(postgres))
        app.state.telemetry.dependencies.labels("redis").set(int(redis))
        response.status_code = 200 if healthy else 503
        return ReadinessResponse(status="ok" if healthy else "unavailable", service=config.service_name,
            postgres=postgres, redis=redis)

    return app
