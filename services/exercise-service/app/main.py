from shared.app import create_app
from shared.config import Settings
from shared.security.api import ERROR_RESPONSES,harden_app,initialize_access
from shared.security.crypto import IdentityCipher
from .routes import router

initialize=initialize_access

def build_app(settings=None):
    app=create_app(settings or Settings(service_name="exercise-service"),initialize=initialize)
    app.version="0.4.0"
    app.description="Exercices contrôlés et évaluations sans notes publiques."
    harden_app(app)
    app.include_router(router,responses=ERROR_RESPONSES)
    return app

app=build_app()
