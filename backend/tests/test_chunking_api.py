import json
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories.document_repository import document_repository
from app.services.chunking import (
    DocumentChunkingService,
    document_chunking_service,
)

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

def test_validate_processed_document_without_sections(
    processed_directory: Path,
) -> None:
    document_id = str(uuid4())

    processed_file = processed_directory / f"{document_id}.json"

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


# NEW TEST STARTS OUTSIDE THE PREVIOUS FUNCTION
def test_split_text_with_overlap():
    text = "A B C D E F G H I J K L M N"

    chunks = DocumentChunkingService._split_text_with_overlap(
        text=text,
        chunk_size=6,
        overlap=2,
    )

    assert chunks == [
        "A B C D E F",
        "E F G H I J",
        "I J K L M N",
    ]


def test_split_text_returns_single_chunk_for_short_text():
    text = "KnowFlow understands enterprise knowledge"

    chunks = DocumentChunkingService._split_text_with_overlap(
        text=text,
        chunk_size=10,
        overlap=2,
    )

    assert chunks == [
        "KnowFlow understands enterprise knowledge",
    ]


def test_split_text_ignores_empty_text():
    chunks = DocumentChunkingService._split_text_with_overlap(
        text="   ",
        chunk_size=10,
        overlap=2,
    )

    assert chunks == []

def test_build_chunk_creates_expected_metadata():
    document_id = "test-document"

    chunk = DocumentChunkingService._build_chunk(
        document_id=document_id,
        chunk_number=1,
        text="KnowFlow   understands enterprise knowledge.",
        source_section_numbers=[2, 3],
        page_numbers=[4],
        metadata={"section_type": "paragraph"},
    )

    assert chunk.document_id == document_id
    assert chunk.chunk_number == 1
    assert chunk.text == (
        "KnowFlow understands enterprise knowledge."
    )
    assert chunk.word_count == 4
    assert chunk.character_count == len(chunk.text)
    assert chunk.token_estimate > 0
    assert chunk.source_section_numbers == [2, 3]
    assert chunk.page_numbers == [4]
    assert chunk.metadata == {
        "section_type": "paragraph"
    }
    assert len(chunk.chunk_id) == 24

def test_build_chunk_id_is_deterministic():
    first_chunk = DocumentChunkingService._build_chunk(
        document_id="document-123",
        chunk_number=1,
        text="KnowFlow retrieves relevant knowledge.",
        source_section_numbers=[1],
    )

    second_chunk = DocumentChunkingService._build_chunk(
        document_id="document-123",
        chunk_number=1,
        text="KnowFlow retrieves relevant knowledge.",
        source_section_numbers=[1],
    )

    assert first_chunk.chunk_id == second_chunk.chunk_id
def test_extract_section_provenance_with_page_number():
    section = {
        "section_number": 7,
        "section_type": "paragraph",
        "text": "KnowFlow preserves document provenance.",
        "metadata": {
            "page_number": 12,
        },
    }

    (
        section_number,
        page_numbers,
        metadata,
    ) = DocumentChunkingService._extract_section_provenance(
        section
    )

    assert section_number == 7
    assert page_numbers == [12]
    assert metadata["page_number"] == 12
    assert metadata["section_type"] == "paragraph"


def test_extract_section_provenance_without_page_number():
    section = {
        "section_number": 3,
        "section_type": "paragraph",
        "text": "TXT sections do not require page numbers.",
        "metadata": {},
    }

    (
        section_number,
        page_numbers,
        metadata,
    ) = DocumentChunkingService._extract_section_provenance(
        section
    )

    assert section_number == 3
    assert page_numbers == []
    assert metadata["section_type"] == "paragraph"
def test_can_group_sections_on_same_page():
    current_section = {
        "metadata": {"page_number": 4},
    }
    next_section = {
        "metadata": {"page_number": 4},
    }

    assert DocumentChunkingService._can_group_sections(
        current_section,
        next_section,
    )


def test_cannot_group_sections_across_pdf_pages():
    current_section = {
        "metadata": {"page_number": 4},
    }
    next_section = {
        "metadata": {"page_number": 5},
    }

    assert not DocumentChunkingService._can_group_sections(
        current_section,
        next_section,
    )


def test_can_group_sections_without_page_numbers():
    current_section = {
        "metadata": {},
    }
    next_section = {
        "metadata": {},
    }

    assert DocumentChunkingService._can_group_sections(
        current_section,
        next_section,
    )
def test_group_sections_combines_short_adjacent_sections():
    sections = [
        {
            "section_number": 1,
            "text": "one two three",
            "metadata": {},
        },
        {
            "section_number": 2,
            "text": "four five",
            "metadata": {},
        },
        {
            "section_number": 3,
            "text": "six seven",
            "metadata": {},
        },
    ]

    groups = DocumentChunkingService._group_sections(
        sections=sections,
        target_words=10,
    )

    assert len(groups) == 1
    assert [
        section["section_number"]
        for section in groups[0]
    ] == [1, 2, 3]


def test_group_sections_respects_target_size():
    sections = [
        {
            "section_number": 1,
            "text": "one two three four",
            "metadata": {},
        },
        {
            "section_number": 2,
            "text": "five six seven four",
            "metadata": {},
        },
    ]

    groups = DocumentChunkingService._group_sections(
        sections=sections,
        target_words=6,
    )

    assert len(groups) == 2
    assert groups[0][0]["section_number"] == 1
    assert groups[1][0]["section_number"] == 2


def test_group_sections_respects_page_boundary():
    sections = [
        {
            "section_number": 1,
            "text": "KnowFlow section one",
            "metadata": {"page_number": 4},
        },
        {
            "section_number": 2,
            "text": "KnowFlow section two",
            "metadata": {"page_number": 5},
        },
    ]

    groups = DocumentChunkingService._group_sections(
        sections=sections,
        target_words=100,
    )

    assert len(groups) == 2
    assert groups[0][0]["section_number"] == 1
    assert groups[1][0]["section_number"] == 2
def test_create_chunks_from_sections_combines_short_sections():
    sections = [
        {
            "section_number": 1,
            "section_type": "paragraph",
            "text": "KnowFlow understands documents.",
            "metadata": {},
        },
        {
            "section_number": 2,
            "section_type": "paragraph",
            "text": "It preserves source knowledge.",
            "metadata": {},
        },
    ]

    chunks = DocumentChunkingService._create_chunks_from_sections(
        document_id="document-123",
        sections=sections,
        chunk_size=20,
        overlap=5,
    )

    assert len(chunks) == 1

    chunk = chunks[0]

    assert chunk.chunk_number == 1
    assert chunk.source_section_numbers == [1, 2]
    assert chunk.text == (
        "KnowFlow understands documents. "
        "It preserves source knowledge."
    )


def test_create_chunks_from_sections_splits_long_text_with_overlap():
    words = [f"word{i}" for i in range(1, 16)]

    sections = [
        {
            "section_number": 1,
            "section_type": "paragraph",
            "text": " ".join(words),
            "metadata": {
                "page_number": 4,
            },
        }
    ]

    chunks = DocumentChunkingService._create_chunks_from_sections(
        document_id="document-123",
        sections=sections,
        chunk_size=6,
        overlap=2,
    )

    assert len(chunks) == 4

    assert chunks[0].text == (
        "word1 word2 word3 word4 word5 word6"
    )
    assert chunks[1].text == (
        "word5 word6 word7 word8 word9 word10"
    )

    assert chunks[0].page_numbers == [4]
    assert chunks[0].source_section_numbers == [1]

    assert chunks[0].chunk_number == 1
    assert chunks[1].chunk_number == 2
    assert chunks[2].chunk_number == 3
    assert chunks[3].chunk_number == 4

def test_split_text_merges_tiny_final_chunk_without_data_loss():
    words = [f"word{i}" for i in range(1, 16)]

    chunks = DocumentChunkingService._split_text_with_overlap(
        text=" ".join(words),
        chunk_size=6,
        overlap=2,
        min_chunk_size=4,
    )

    assert chunks == [
        "word1 word2 word3 word4 word5 word6",
        "word5 word6 word7 word8 word9 word10",
        (
            "word9 word10 word11 word12 "
            "word13 word14 word15"
        ),
    ]

    assert "word15" in chunks[-1]
def test_chunk_document_creates_chunks(
    processed_directory: Path,
) -> None:
    document_id = str(uuid4())

    payload = {
        "document_id": document_id,
        "sections": [
            {
                "section_number": 1,
                "section_type": "paragraph",
                "text": (
                    "KnowFlow converts processed document "
                    "sections into retrieval-ready chunks."
                ),
                "character_count": 78,
                "word_count": 8,
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

    chunks = document_chunking_service.chunk_document(
        document_id
    )

    assert len(chunks) == 1

    chunk = chunks[0]

    assert chunk.document_id == document_id
    assert chunk.chunk_number == 1
    assert chunk.source_section_numbers == [1]
    assert chunk.text.startswith("KnowFlow converts")