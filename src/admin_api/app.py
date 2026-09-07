from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:4321"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type"],
    )

    app.state.neddex_application = application

    app.include_router(health_router)
    app.include_router(vehicles_router)

    return app


app = create_app()