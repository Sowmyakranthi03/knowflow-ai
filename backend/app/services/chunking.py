from typing import Any

from app.core.config import settings
from app.core.exceptions import (
    DocumentChunkingError,
    DocumentProcessingError,
)
from app.repositories.document_repository import (
    DocumentRepository,
    document_repository,
)
from app.schemas.chunk import ChunkingConfigurationResponse


class DocumentChunkingService:
    def __init__(
        self,
        repository: DocumentRepository,
    ) -> None:
        self.repository = repository

    def validate_processed_document(
        self,
        document_id: str,
    ) -> dict[str, Any]:
        try:
            processed_document = (
                self.repository.load_processed_document(document_id)
            )

        except DocumentProcessingError as error:
            raise DocumentChunkingError(
                error.message,
                status_code=error.status_code,
                error_code=error.error_code,
            ) from error

        sections = processed_document.get("sections")

        if not isinstance(sections, list):
            raise DocumentChunkingError(
                "The processed document does not contain valid sections.",
                status_code=422,
                error_code="INVALID_PROCESSED_SECTIONS",
            )

        if not sections:
            raise DocumentChunkingError(
                "The processed document does not contain any sections.",
                status_code=422,
                error_code="NO_SECTIONS_AVAILABLE",
            )

        return processed_document

    @staticmethod
    def get_configuration() -> ChunkingConfigurationResponse:
        return ChunkingConfigurationResponse(
            chunk_size_words=settings.chunk_size_words,
            chunk_overlap_words=settings.chunk_overlap_words,
            min_chunk_size_words=settings.min_chunk_size_words,
            max_chunks_per_document=settings.max_chunks_per_document,
        )


document_chunking_service = DocumentChunkingService(
    repository=document_repository
)