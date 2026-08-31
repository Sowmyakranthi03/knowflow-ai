import json
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories.document_repository import document_repository


client = TestClient(app)


@pytest.fixture
def processed_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    directory = tmp_path / "processed"
    directory.mkdir()

    monkeypatch.setattr(
        document_repository,
        "processed_directory",
        directory,
    )

    return directory


def test_get_chunking_configuration() -> None:
    response = client.get(
        "/api/v1/documents/chunking/configuration"
    )

    assert response.status_code == 200
    assert response.json() == {
        "chunk_size_words": 180,
        "chunk_overlap_words": 30,
        "min_chunk_size_words": 40,
        "max_chunks_per_document": 10000,
    }


def test_validate_processed_document_for_chunking(
    processed_directory: Path,
) -> None:
    document_id = str(uuid4())

    payload = {
        "document_id": document_id,
        "sections": [
            {
                "section_number": 1,
                "section_type": "paragraph",
                "text": "KnowFlow AI processes enterprise documents.",
                "character_count": 45,
                "word_count": 5,
                "metadata": {},
            }
        ],
    }

    processed_file = (
        processed_directory / f"{document_id}.json"
    )

    processed_file.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    response = client.post(
        f"/api/v1/documents/{document_id}/chunk/validate"
    )

    assert response.status_code == 200
    assert response.json() == {
        "document_id": document_id,
        "status": "ready_for_chunking",
        "sections_available": 1,
    }


def test_validate_unprocessed_document(
    processed_directory: Path,
) -> None:
    document_id = str(uuid4())

    response = client.post(
        f"/api/v1/documents/{document_id}/chunk/validate"
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == (
        "DOCUMENT_NOT_PROCESSED"
    )


def test_validate_processed_document_without_sections(
    processed_directory: Path,
) -> None:
    document_id = str(uuid4())

    processed_file = (
        processed_directory / f"{document_id}.json"
    )

    processed_file.write_text(
        json.dumps(
            {
                "document_id": document_id,
                "sections": [],
            }
        ),
        encoding="utf-8",
    )

    response = client.post(
        f"/api/v1/documents/{document_id}/chunk/validate"
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == (
        "NO_SECTIONS_AVAILABLE"
    )