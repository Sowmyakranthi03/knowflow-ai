import logging
from datetime import UTC, datetime
from pathlib import Path

from app.core.exceptions import DocumentProcessingError
from app.repositories.document_repository import (
    DocumentRepository,
    document_repository,
)
from app.schemas.document import (
    DocumentProcessingResponse,
    DocumentStatistics,
    ExtractedSection,
)
from app.services.document_parsers import DocumentParserFactory


logger = logging.getLogger(__name__)


class DocumentProcessingService:
    def __init__(
        self,
        repository: DocumentRepository,
    ) -> None:
        self.repository = repository

    def process_document(
        self,
        document_id: str,
    ) -> DocumentProcessingResponse:
        document_path = self.repository.find_document(document_id)
        extension = document_path.suffix.lower()

        parser = DocumentParserFactory.get_parser(extension)

        logger.info(
            "Document processing started | document_id=%s | parser=%s",
            document_id,
            parser.parser_name,
        )

        sections = parser.parse(document_path)
        full_text = self._build_full_text(sections)
        statistics = self._calculate_statistics(
            extension=extension,
            sections=sections,
        )

        if not full_text.strip():
            raise DocumentProcessingError(
                (
                    "No extractable text was found. "
                    "The document may contain scanned images only."
                ),
                status_code=422,
                error_code="NO_EXTRACTABLE_TEXT",
            )

        processed_at = datetime.now(UTC)

        provisional_response = DocumentProcessingResponse(
            document_id=document_id,
            stored_filename=document_path.name,
            file_extension=extension,
            parser=parser.parser_name,
            status="processed",
            processed_at=processed_at,
            full_text=full_text,
            sections=sections,
            statistics=statistics,
            processed_output_path="",
        )

        output_path = self.repository.save_processed_document(
            document_id=document_id,
            payload=provisional_response.model_dump(mode="json"),
        )

        response = provisional_response.model_copy(
            update={
                "processed_output_path": self._display_path(output_path),
            }
        )

        self.repository.save_processed_document(
            document_id=document_id,
            payload=response.model_dump(mode="json"),
        )

        logger.info(
            (
                "Document processing completed | "
                "document_id=%s | sections=%s | words=%s"
            ),
            document_id,
            statistics.section_count,
            statistics.word_count,
        )

        return response

    @staticmethod
    def _build_full_text(
        sections: list[ExtractedSection],
    ) -> str:
        return "\n\n".join(
            section.text
            for section in sections
            if section.text
        ).strip()

    @staticmethod
    def _calculate_statistics(
        *,
        extension: str,
        sections: list[ExtractedSection],
    ) -> DocumentStatistics:
        page_count = None
        paragraph_count = None
        table_count = None

        if extension == ".pdf":
            page_count = sum(
                section.section_type == "page"
                for section in sections
            )

        if extension in {".docx", ".txt"}:
            paragraph_count = sum(
                section.section_type == "paragraph"
                for section in sections
            )

        if extension == ".docx":
            table_count = sum(
                section.section_type == "table"
                for section in sections
            )

        return DocumentStatistics(
            section_count=len(sections),
            page_count=page_count,
            paragraph_count=paragraph_count,
            table_count=table_count,
            character_count=sum(
                section.character_count
                for section in sections
            ),
            word_count=sum(
                section.word_count
                for section in sections
            ),
            empty_section_count=sum(
                not section.text.strip()
                for section in sections
            ),
        )

    @staticmethod
    def _display_path(output_path: Path) -> str:
        return output_path.as_posix()


document_processing_service = DocumentProcessingService(
    repository=document_repository
)