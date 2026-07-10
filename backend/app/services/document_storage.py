import logging
import os
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import DocumentUploadError
from app.schemas.document import DocumentUploadResponse


logger = logging.getLogger(__name__)

PDF_SIGNATURE = b"%PDF-"
ZIP_SIGNATURES = (
    b"PK\x03\x04",
    b"PK\x05\x06",
    b"PK\x07\x08",
)


class DocumentStorageService:
    def __init__(self, upload_directory: Path) -> None:
        self.upload_directory = upload_directory

    async def save_document(
        self,
        uploaded_file: UploadFile,
    ) -> DocumentUploadResponse:
        original_filename = self._validate_filename(
            uploaded_file.filename
        )

        extension = Path(original_filename).suffix.lower()

        self._validate_extension(extension)
        self._validate_content_type(uploaded_file.content_type)

        document_id = str(uuid4())
        stored_filename = f"{document_id}{extension}"
        destination = self.upload_directory / stored_filename

        self.upload_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:
            size_bytes = await self._write_file(
                uploaded_file=uploaded_file,
                destination=destination,
            )

            self._validate_file_contents(
                destination=destination,
                extension=extension,
            )

        except DocumentUploadError:
            self._remove_file_if_present(destination)
            raise

        except OSError as error:
            self._remove_file_if_present(destination)

            logger.exception(
                "Unable to store uploaded document: %s",
                original_filename,
            )

            raise DocumentUploadError(
                "The document could not be stored.",
                status_code=500,
                error_code="DOCUMENT_STORAGE_ERROR",
            ) from error

        finally:
            await uploaded_file.close()

        uploaded_at = datetime.now(UTC)

        logger.info(
            (
                "Document uploaded successfully | "
                "document_id=%s | original_filename=%s | "
                "stored_filename=%s | size_bytes=%s"
            ),
            document_id,
            original_filename,
            stored_filename,
            size_bytes,
        )

        return DocumentUploadResponse(
            document_id=document_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_extension=extension,
            content_type=self._normalise_content_type(
                extension=extension,
                provided_content_type=uploaded_file.content_type,
            ),
            size_bytes=size_bytes,
            size_mb=round(size_bytes / (1024 * 1024), 4),
            uploaded_at=uploaded_at,
            status="uploaded",
        )

    async def _write_file(
        self,
        uploaded_file: UploadFile,
        destination: Path,
    ) -> int:
        total_size = 0

        with destination.open("wb") as output_file:
            while chunk := await uploaded_file.read(
                settings.upload_chunk_size_bytes
            ):
                total_size += len(chunk)

                if total_size > settings.max_upload_size_bytes:
                    raise DocumentUploadError(
                        (
                            "File size exceeds the "
                            f"{settings.max_upload_size_mb} MB limit."
                        ),
                        status_code=413,
                        error_code="FILE_TOO_LARGE",
                    )

                output_file.write(chunk)

        if total_size == 0:
            raise DocumentUploadError(
                "The uploaded file is empty.",
                status_code=400,
                error_code="EMPTY_FILE",
            )

        return total_size

    @staticmethod
    def _validate_filename(filename: str | None) -> str:
        if filename is None or not filename.strip():
            raise DocumentUploadError(
                "A valid filename is required.",
                status_code=400,
                error_code="INVALID_FILENAME",
            )

        clean_filename = Path(filename).name.strip()

        if clean_filename in {"", ".", ".."}:
            raise DocumentUploadError(
                "A valid filename is required.",
                status_code=400,
                error_code="INVALID_FILENAME",
            )

        return clean_filename

    @staticmethod
    def _validate_extension(extension: str) -> None:
        if extension not in settings.allowed_document_extensions:
            raise DocumentUploadError(
                "Only PDF, DOCX, and TXT files are supported.",
                status_code=415,
                error_code="UNSUPPORTED_FILE_TYPE",
            )

    @staticmethod
    def _validate_content_type(
        content_type: str | None,
    ) -> None:
        if content_type is None:
            return

        normalized_content_type = (
            content_type.split(";", maxsplit=1)[0]
            .strip()
            .lower()
        )

        if (
            normalized_content_type
            not in settings.allowed_document_mime_types
        ):
            raise DocumentUploadError(
                "The uploaded file has an unsupported content type.",
                status_code=415,
                error_code="UNSUPPORTED_CONTENT_TYPE",
            )

    def _validate_file_contents(
        self,
        destination: Path,
        extension: str,
    ) -> None:
        if extension == ".pdf":
            self._validate_pdf(destination)
            return

        if extension == ".docx":
            self._validate_docx(destination)
            return

        if extension == ".txt":
            self._validate_txt(destination)
            return

        raise DocumentUploadError(
            "Unsupported document format.",
            status_code=415,
            error_code="UNSUPPORTED_FILE_TYPE",
        )

    @staticmethod
    def _validate_pdf(destination: Path) -> None:
        with destination.open("rb") as document:
            signature = document.read(len(PDF_SIGNATURE))

        if signature != PDF_SIGNATURE:
            raise DocumentUploadError(
                "The uploaded file is not a valid PDF document.",
                status_code=400,
                error_code="INVALID_PDF_FILE",
            )

    @staticmethod
    def _validate_docx(destination: Path) -> None:
        with destination.open("rb") as document:
            signature = document.read(4)

        if not any(
            signature.startswith(zip_signature)
            for zip_signature in ZIP_SIGNATURES
        ):
            raise DocumentUploadError(
                "The uploaded file is not a valid DOCX document.",
                status_code=400,
                error_code="INVALID_DOCX_FILE",
            )

        try:
            with zipfile.ZipFile(destination) as archive:
                filenames = set(archive.namelist())

                required_entries = {
                    "[Content_Types].xml",
                    "word/document.xml",
                }

                if not required_entries.issubset(filenames):
                    raise DocumentUploadError(
                        "The uploaded file is not a valid DOCX document.",
                        status_code=400,
                        error_code="INVALID_DOCX_FILE",
                    )

        except zipfile.BadZipFile as error:
            raise DocumentUploadError(
                "The uploaded file is not a valid DOCX document.",
                status_code=400,
                error_code="INVALID_DOCX_FILE",
            ) from error

    @staticmethod
    def _validate_txt(destination: Path) -> None:
        try:
            content = destination.read_bytes()

            if b"\x00" in content:
                raise DocumentUploadError(
                    "The uploaded TXT file contains binary data.",
                    status_code=400,
                    error_code="INVALID_TEXT_FILE",
                )

            content.decode("utf-8")

        except UnicodeDecodeError as error:
            raise DocumentUploadError(
                "TXT documents must use UTF-8 encoding.",
                status_code=400,
                error_code="INVALID_TEXT_ENCODING",
            ) from error

    @staticmethod
    def _normalise_content_type(
        extension: str,
        provided_content_type: str | None,
    ) -> str:
        canonical_types = {
            ".pdf": "application/pdf",
            ".docx": (
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
            ".txt": "text/plain",
        }

        return canonical_types.get(
            extension,
            provided_content_type or "application/octet-stream",
        )

    @staticmethod
    def _remove_file_if_present(destination: Path) -> None:
        try:
            if destination.exists():
                os.remove(destination)

        except OSError:
            logger.exception(
                "Unable to remove incomplete upload: %s",
                destination,
            )


document_storage_service = DocumentStorageService(
    upload_directory=settings.upload_directory
)