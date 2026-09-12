from shared.app import create_app
from shared.config import Settings
from shared.security.api import ERROR_RESPONSES, harden_app, initialize_access
from .routes import router

def build_app(settings=None):
    application = create_app(settings or Settings(service_name="curriculum-service"), initialize=initialize_access)
    application.version = "0.3.0"
    application.description = "Référentiel Cycle 3, domaines et graphe de prérequis acyclique."
    harden_app(application)
    application.include_router(router, responses=ERROR_RESPONSES)
    return application

app = build_app()
