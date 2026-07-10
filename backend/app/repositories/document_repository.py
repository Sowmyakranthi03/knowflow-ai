import json
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.exceptions import DocumentProcessingError


class DocumentRepository:
    def __init__(
        self,
        upload_directory: Path,
        processed_directory: Path,
    ) -> None:
        self.upload_directory = upload_directory
        self.processed_directory = processed_directory

    def find_document(self, document_id: str) -> Path:
        self._validate_document_id(document_id)

        matches: list[Path] = []

        for extension in settings.allowed_document_extensions:
            candidate = self.upload_directory / f"{document_id}{extension}"

            if candidate.is_file():
                matches.append(candidate)

        if not matches:
            raise DocumentProcessingError(
                "The requested document could not be found.",
                status_code=404,
                error_code="DOCUMENT_NOT_FOUND",
            )

        if len(matches) > 1:
            raise DocumentProcessingError(
                "Multiple stored documents have the same identifier.",
                status_code=409,
                error_code="DOCUMENT_ID_CONFLICT",
            )

        return matches[0]

    def save_processed_document(
        self,
        document_id: str,
        payload: dict[str, Any],
    ) -> Path:
        self.processed_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = self.processed_directory / f"{document_id}.json"
        temporary_path = self.processed_directory / f"{document_id}.json.tmp"

        try:
            temporary_path.write_text(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                ),
                encoding="utf-8",
            )

            temporary_path.replace(output_path)

        except OSError as error:
            temporary_path.unlink(missing_ok=True)

            raise DocumentProcessingError(
                "Processed document data could not be stored.",
                status_code=500,
                error_code="PROCESSED_DOCUMENT_STORAGE_ERROR",
            ) from error

        return output_path

    @staticmethod
    def _validate_document_id(document_id: str) -> None:
        if not document_id:
            raise DocumentProcessingError(
                "A document identifier is required.",
                status_code=400,
                error_code="INVALID_DOCUMENT_ID",
            )

        allowed_characters = set(
            "0123456789abcdefABCDEF-"
        )

        if any(
            character not in allowed_characters
            for character in document_id
        ):
            raise DocumentProcessingError(
                "The document identifier is invalid.",
                status_code=400,
                error_code="INVALID_DOCUMENT_ID",
            )


document_repository = DocumentRepository(
    upload_directory=settings.upload_directory,
    processed_directory=settings.processed_directory,
)