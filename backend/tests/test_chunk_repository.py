from pathlib import Path

import pytest

from app.core.exceptions import DocumentChunkingError
from app.repositories.chunk_repository import ChunkRepository


def test_save_and_load_chunks(
    tmp_path: Path,
) -> None:
    repository = ChunkRepository(
        chunks_directory=tmp_path,
    )

    document_id = "12345678-1234-1234-1234-123456789abc"

    payload = {
        "document_id": document_id,
        "status": "chunked",
        "chunks": [
            {
                "chunk_id": f"{document_id}_chunk_0001",
                "text": "KnowFlow AI chunk content.",
            }
        ],
    }

    output_path = repository.save_chunks(
        document_id=document_id,
        payload=payload,
    )

    assert output_path.exists()
    assert output_path.name == f"{document_id}.json"

    loaded_payload = repository.load_chunks(document_id)

    assert loaded_payload == payload


def test_load_missing_chunks(
    tmp_path: Path,
) -> None:
    repository = ChunkRepository(
        chunks_directory=tmp_path,
    )

    with pytest.raises(DocumentChunkingError) as error:
        repository.load_chunks(
            "12345678-1234-1234-1234-123456789abc"
        )

    assert error.value.error_code == "CHUNKS_NOT_FOUND"
    assert error.value.status_code == 404


def test_load_invalid_chunk_json(
    tmp_path: Path,
) -> None:
    repository = ChunkRepository(
        chunks_directory=tmp_path,
    )

    document_id = "12345678-1234-1234-1234-123456789abc"

    invalid_file = tmp_path / f"{document_id}.json"
    invalid_file.write_text(
        "{not valid json",
        encoding="utf-8",
    )

    with pytest.raises(DocumentChunkingError) as error:
        repository.load_chunks(document_id)

    assert error.value.error_code == "INVALID_CHUNK_DATA"