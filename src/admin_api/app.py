from pathlib import Path

from fastapi import FastAPI

from src.admin_api.routes.health import router as health_router
from src.admin_api.routes.vehicles import router as vehicles_router
from src.application import NeddexApplication


DATABASE_PATH = Path("data/neddex.db")


def create_app(
    database_path: Path = DATABASE_PATH,
) -> FastAPI:
    application = NeddexApplication(database_path)
    application.initialize()

    app = FastAPI(title="Neddex Admin API")

    app.state.neddex_application = application

    app.include_router(health_router)
    app.include_router(vehicles_router)

    return app


app = create_app()