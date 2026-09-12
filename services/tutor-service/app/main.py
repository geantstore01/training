from shared.app import create_app
from shared.config import Settings
from shared.ai.transport import install_errors
from shared.security.api import ERROR_RESPONSES, harden_app, initialize_access
from .routes import router

def build_app(settings=None):
    app = create_app(settings or Settings(service_name="tutor-service"), initialize=initialize_access)
    app.version = "0.6.0"
    app.description = "Capitaine Savoir : sept niveaux 0–6, sources validées et messages pédagogiques contrôlés."
    harden_app(app)
    install_errors(app)
    app.include_router(router, responses=ERROR_RESPONSES)
    return app

app = build_app()
