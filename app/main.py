from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import v1_router
from app.core.config import get_settings
from app.core.database import check_db_health, get_engine, init_engine
from app.exceptions.handlers import register_exception_handlers
from app.middleware.cors import setup_cors
from app.middleware.logging import LoggingMiddleware
from app.schemas.common import HealthResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: startup and shutdown events."""
    settings = get_settings()
    init_engine(settings)
    logger.info("Starting up %s", app.title)
    yield
    logger.info("Shutting down %s", app.title)
    await get_engine().dispose()


def create_app() -> FastAPI:
    """Application factory: creates and configures the FastAPI instance."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    # Middleware (order matters: outermost first)
    app.add_middleware(LoggingMiddleware)
    setup_cors(app, settings)

    # Exception handlers
    register_exception_handlers(app)

    # Routes
    app.include_router(v1_router)

    @app.get("/health", response_model=HealthResponse, tags=["health"])
    async def health() -> HealthResponse:
        db_ok = await check_db_health()
        return HealthResponse(status="ok" if db_ok else "degraded", database_connected=db_ok)

    return app
