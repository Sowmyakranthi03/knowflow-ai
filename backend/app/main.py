import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.core.config import settings
from app.core.logging import configure_logging


configure_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "Starting %s version %s",
        settings.app_name,
        settings.app_version,
    )

    yield

    logger.info(
        "Shutting down %s",
        settings.app_name,
    )


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    debug=settings.debug,
    lifespan=lifespan,
)


app.include_router(
    health_router,
    prefix=settings.api_v1_prefix,
)


@app.get(
    "/",
    tags=["Root"],
    summary="API root",
    description="Returns basic information about the KnowFlow AI API.",
)
async def root() -> dict[str, str]:
    return {
        "message": f"{settings.app_name} API is running",
        "documentation": "/docs",
        "health": f"{settings.api_v1_prefix}/health",
    }