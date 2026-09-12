from shared.app import create_app
from shared.config import Settings
from shared.security.api import ERROR_RESPONSES, harden_app, initialize_access
from .routes import router


def build_app(settings=None):
    application = create_app(settings or Settings(service_name="auth-service"),
        initialize=lambda app: initialize_access(app, signing=True))
    application.version = "0.2.0"
    application.description = "JWT RS256, refresh tokens Redis à rotation unique et révocation immédiate."
    harden_app(application)
    application.include_router(router, responses=ERROR_RESPONSES)
    return application


app = build_app()
