import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.documents import router as documents_router
from app.api.routes.health import router as health_router
from app.core.config import settings
from app.core.exception_handlers import (
    document_chunking_exception_handler,
    document_processing_exception_handler,
    document_upload_exception_handler,
)
from app.core.exceptions import (
    DocumentChunkingError,
    DocumentProcessingError,
    DocumentUploadError,
)
from app.core.logging import configure_logging


configure_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings.upload_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    settings.processed_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    settings.chunks_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    logger.info(
        "Starting %s version %s",
        settings.app_name,
        settings.app_version,
    )

    logger.info(
        "Document storage directory: %s",
        settings.upload_directory,
    )

    logger.info(
        "Processed document directory: %s",
        settings.processed_directory,
    )

    logger.info(
        "Chunk storage directory: %s",
        settings.chunks_directory,
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

app.add_exception_handler(
    DocumentUploadError,
    document_upload_exception_handler,
)

app.add_exception_handler(
    DocumentProcessingError,
    document_processing_exception_handler,
)

app.add_exception_handler(
    DocumentChunkingError,
    document_chunking_exception_handler,
)

app.include_router(
    health_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    documents_router,
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
        "documents": f"{settings.api_v1_prefix}/documents",
    }