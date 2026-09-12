from shared.app import create_app
from shared.config import Settings
from shared.security.api import ERROR_RESPONSES, harden_app, initialize_access
from shared.security.crypto import IdentityCipher
from .routes import router


def initialize(app):
    initialize_access(app)
    app.state.cipher = IdentityCipher(app.state.settings.pii_keys_file)


def build_app(settings=None):
    application = create_app(settings or Settings(service_name="user-service"), initialize=initialize)
    application.version = "0.2.0"
    application.description = "Profils par école, liens parentaux vérifiés et registre de consentements append-only."
    harden_app(application)
    application.include_router(router, responses=ERROR_RESPONSES)
    return application


app = build_app()
