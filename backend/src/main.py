from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.administration.presentation.auth_routes import router as admin_auth_router
from src.administration.presentation.quote_routes import router as admin_quotes_router
from src.catalog.presentation.routes import router as catalog_router
from src.materials.presentation.admin_routes import router as admin_materials_router
from src.materials.presentation.routes import router as materials_router
from src.notifications.presentation.admin_routes import router as admin_notifications_router
from src.quotes.presentation.routes import router as quotes_router
from src.reporting.presentation.routes import router as reporting_router

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def create_app() -> FastAPI:
    app = FastAPI(title="3D-Lab", version="0.1.0")
    app.mount(
        "/static",
        StaticFiles(directory=PROJECT_ROOT / "frontend" / "src"),
        name="static",
    )
    app.include_router(catalog_router)
    app.include_router(materials_router)
    app.include_router(quotes_router)
    app.include_router(admin_auth_router)
    app.include_router(admin_quotes_router)
    app.include_router(admin_materials_router)
    app.include_router(admin_notifications_router)
    app.include_router(reporting_router)
    return app


app = create_app()
