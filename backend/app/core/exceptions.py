class KnowFlowError(Exception):
    """Base exception for application-specific errors."""


class DocumentUploadError(KnowFlowError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int = 400,
        error_code: str = "DOCUMENT_UPLOAD_ERROR",
    ) -> None:
        super().__init__(message)

        self.message = message
        self.status_code = status_code
        self.error_code = error_code


class DocumentProcessingError(KnowFlowError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int = 400,
        error_code: str = "DOCUMENT_PROCESSING_ERROR",
    ) -> None:
        super().__init__(message)

        self.message = message
        self.status_code = status_code
        self.error_code = error_code