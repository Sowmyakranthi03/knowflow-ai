import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    DocumentProcessingError,
    DocumentUploadError,
)


logger = logging.getLogger(__name__)


async def document_upload_exception_handler(
    request: Request,
    exception: DocumentUploadError,
) -> JSONResponse:
    logger.warning(
        "Document upload rejected | path=%s | code=%s | reason=%s",
        request.url.path,
        exception.error_code,
        exception.message,
    )

    return JSONResponse(
        status_code=exception.status_code,
        content={
            "error": {
                "code": exception.error_code,
                "message": exception.message,
            }
        },
    )


async def document_processing_exception_handler(
    request: Request,
    exception: DocumentProcessingError,
) -> JSONResponse:
    logger.warning(
        "Document processing failed | path=%s | code=%s | reason=%s",
        request.url.path,
        exception.error_code,
        exception.message,
    )

    return JSONResponse(
        status_code=exception.status_code,
        content={
            "error": {
                "code": exception.error_code,
                "message": exception.message,
            }
        },
    )