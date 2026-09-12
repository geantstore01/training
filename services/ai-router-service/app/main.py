from shared.app import create_app
from shared.config import Settings
from shared.ai.transport import Circuit, install_errors
from shared.security.api import ERROR_RESPONSES, harden_app, initialize_access
from .routes import router

def initialize(app):
    initialize_access(app)
    app.state.circuit = Circuit()

def build_app(settings=None):
    app = create_app(settings or Settings(service_name="ai-router-service"), initialize=initialize)
    app.version = "0.6.0"
    app.description = "Planification pédagogique Ollama Cloud ; accès interservices, consentement et validation stricte."
    harden_app(app)
    install_errors(app)
    app.include_router(router, responses=ERROR_RESPONSES)
    return app

app = build_app()
