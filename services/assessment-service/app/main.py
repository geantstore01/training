from shared.app import create_app
from shared.config import Settings
from shared.security.api import ERROR_RESPONSES,harden_app,initialize_access
from shared.security.crypto import IdentityCipher
from .routes import router
from .science import router as science_router
from .history import router as history_router

def initialize(app):
    initialize_access(app)
    app.state.cipher=IdentityCipher(app.state.settings.pii_keys_file)

def build_app(settings=None):
    app=create_app(settings or Settings(service_name="assessment-service"),initialize=initialize)
    app.version="0.4.0"
    app.description="Exercices contrôlés et évaluations sans notes publiques."
    harden_app(app)
    app.include_router(router,responses=ERROR_RESPONSES)
    app.include_router(science_router,responses=ERROR_RESPONSES)
    app.include_router(history_router,responses=ERROR_RESPONSES)
    return app

app=build_app()
