import json
from pathlib import Path
from typing import Any

from app.core.exceptions import DocumentChunkingError
from app.core.config import settings


class ChunkRepository:
    def __init__(
        self,
        chunks_directory: Path,
    ) -> None:
        self.chunks_directory = chunks_directory

    def save_chunks(
        self,
        document_id: str,
        payload: dict[str, Any],
    ) -> Path:
        self.chunks_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = self.chunks_directory / f"{document_id}.json"
        temporary_path = (
            self.chunks_directory / f"{document_id}.json.tmp"
        )

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

            raise DocumentChunkingError(
                "Chunk data could not be stored.",
                status_code=500,
                error_code="CHUNK_STORAGE_ERROR",
            ) from error

        return output_path

    def load_chunks(
        self,
        document_id: str,
    ) -> dict[str, Any]:
        output_path = self.chunks_directory / f"{document_id}.json"

        if not output_path.is_file():
            raise DocumentChunkingError(
                "Chunk data could not be found.",
                status_code=404,
                error_code="CHUNKS_NOT_FOUND",
            )

        try:
            payload = json.loads(
                output_path.read_text(encoding="utf-8")
            )

        except json.JSONDecodeError as error:
            raise DocumentChunkingError(
                "Stored chunk data is invalid.",
                status_code=500,
                error_code="INVALID_CHUNK_DATA",
            ) from error

        except OSError as error:
            raise DocumentChunkingError(
                "Stored chunk data could not be read.",
                status_code=500,
                error_code="CHUNK_READ_ERROR",
            ) from error

        if not isinstance(payload, dict):
            raise DocumentChunkingError(
                "Stored chunk data is invalid.",
                status_code=500,
                error_code="INVALID_CHUNK_DATA",
            )

        return payload

chunk_repository = ChunkRepository(
    chunks_directory=settings.chunks_directory
)