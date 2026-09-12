from shared.app import create_app
from shared.config import Settings
from shared.security.api import ERROR_RESPONSES, harden_app, initialize_access
from .routes import router
from .history import router as history_router
from .french import router as french_router

def build_app(settings=None):
    application = create_app(settings or Settings(service_name="content-service"), initialize=initialize_access)
    application.version = "0.3.0"
    application.description = "Contenus versionnés et publication après validation humaine indépendante."
    harden_app(application)
    application.include_router(router, responses=ERROR_RESPONSES)
    application.include_router(history_router,responses=ERROR_RESPONSES)
    application.include_router(french_router,responses=ERROR_RESPONSES)
    return application

app = build_app()
