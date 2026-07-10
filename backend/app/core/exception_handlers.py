import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import DocumentUploadError


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