from shared.app import create_app
from shared.config import Settings
from shared.security.api import ERROR_RESPONSES,harden_app,initialize_access
from shared.ai.transport import install_errors
from .routes import router

def build_app(settings=None):
    app=create_app(settings or Settings(service_name="notification-service"),initialize=initialize_access)
    app.version="0.8.0"
    app.description="ÉDUCAPILOTE : suivi scolaire, administration et accessibilité sécurisés."
    harden_app(app)
    install_errors(app)
    app.include_router(router,responses=ERROR_RESPONSES)
    return app

app=build_app()
