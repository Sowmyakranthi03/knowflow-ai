from datetime import datetime, timezone
from hashlib import sha256
from math import ceil
from typing import Any

from app.core.config import settings
from app.core.exceptions import (
    DocumentChunkingError,
    DocumentProcessingError,
)
from app.repositories.chunk_repository import (
    ChunkRepository,
    chunk_repository,
)
from app.repositories.document_repository import (
    DocumentRepository,
    document_repository,
)
from app.schemas.chunk import (
    ChunkingConfigurationResponse,
    ChunkingResponse,
    ChunkingStatistics,
    DocumentChunk,
)


class DocumentChunkingService:
    def __init__(
        self,
        repository: DocumentRepository,
        chunk_repository: ChunkRepository,
    ) -> None:
        self.repository = repository
        self.chunk_repository = chunk_repository

    @staticmethod
    def _split_text_with_overlap(
        text: str,
        chunk_size: int,
        overlap: int,
        min_chunk_size: int = 0,
    ) -> list[str]:
        """Split text into word-based chunks with overlap."""
        words = text.split()

        if not words:
            return []

        if len(words) <= chunk_size:
            return [" ".join(words)]

        chunks: list[str] = []
        step = chunk_size - overlap

        for start in range(0, len(words), step):
            end = start + chunk_size
            chunk_words = words[start:end]

            if not chunk_words:
                break

            chunks.append(" ".join(chunk_words))

            if end >= len(words):
                break

        if (
            len(chunks) > 1
            and min_chunk_size > 0
            and len(chunks[-1].split()) < min_chunk_size
        ):
            previous_words = chunks[-2].split()
            final_words = chunks[-1].split()

            overlap_words = min(
                overlap,
                len(previous_words),
                len(final_words),
            )

            tail_words = final_words[overlap_words:]

            if tail_words:
                chunks[-2] = " ".join(
                    previous_words + tail_words
                )

            chunks.pop()

        return chunks

    @staticmethod
    def _build_chunk(
        document_id: str,
        chunk_number: int,
        text: str,
        source_section_numbers: list[int],
        page_numbers: list[int] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DocumentChunk:
        """Create a validated document chunk with deterministic metadata."""
        normalized_text = " ".join(text.split())

        word_count = len(normalized_text.split())
        character_count = len(normalized_text)

        token_estimate = (
            ceil(character_count / 4)
            if character_count
            else 0
        )

        chunk_identity = (
            f"{document_id}:{chunk_number}:{normalized_text}"
        )

        chunk_id = sha256(
            chunk_identity.encode("utf-8")
        ).hexdigest()[:24]

        return DocumentChunk(
            chunk_id=chunk_id,
            document_id=document_id,
            chunk_number=chunk_number,
            text=normalized_text,
            word_count=word_count,
            character_count=character_count,
            token_estimate=token_estimate,
            source_section_numbers=source_section_numbers,
            page_numbers=page_numbers or [],
            metadata=metadata or {},
        )

    @staticmethod
    def _calculate_statistics(
        chunks: list[DocumentChunk],
    ) -> ChunkingStatistics:
        """Calculate statistics for generated document chunks."""
        if not chunks:
            raise DocumentChunkingError(
                "Chunk statistics cannot be calculated without chunks.",
                status_code=422,
                error_code="NO_CHUNKS_FOR_STATISTICS",
            )

        word_counts = [
            chunk.word_count
            for chunk in chunks
        ]

        return ChunkingStatistics(
            chunks_created=len(chunks),
            total_words=sum(word_counts),
            total_characters=sum(
                chunk.character_count
                for chunk in chunks
            ),
            average_chunk_words=round(
                sum(word_counts) / len(chunks),
                2,
            ),
            smallest_chunk_words=min(word_counts),
            largest_chunk_words=max(word_counts),
            configured_chunk_size_words=(
                settings.chunk_size_words
            ),
            configured_overlap_words=(
                settings.chunk_overlap_words
            ),
        )

    @staticmethod
    def _extract_section_provenance(
        section: dict[str, Any],
    ) -> tuple[int, list[int], dict[str, Any]]:
        """Extract source section, page numbers, and metadata."""
        section_number = section.get("section_number")
        section_type = section.get("section_type")
        section_metadata = section.get(
            "metadata",
            {},
        )

        if not isinstance(section_number, int):
            raise DocumentChunkingError(
                "Processed section is missing a valid section number.",
                status_code=422,
                error_code="INVALID_SECTION_NUMBER",
            )

        if not isinstance(section_metadata, dict):
            section_metadata = {}

        page_numbers: list[int] = []

        page_number = section_metadata.get(
            "page_number"
        )

        if isinstance(page_number, int):
            page_numbers.append(page_number)

        metadata = dict(section_metadata)

        if isinstance(section_type, str):
            metadata["section_type"] = section_type

        return (
            section_number,
            page_numbers,
            metadata,
        )

    @staticmethod
    def _can_group_sections(
        current_section: dict[str, Any],
        next_section: dict[str, Any],
    ) -> bool:
        """Determine whether two adjacent sections can share a chunk."""
        current_metadata = current_section.get(
            "metadata",
            {},
        )
        next_metadata = next_section.get(
            "metadata",
            {},
        )

        if not isinstance(current_metadata, dict):
            current_metadata = {}

        if not isinstance(next_metadata, dict):
            next_metadata = {}

        current_page = current_metadata.get(
            "page_number"
        )
        next_page = next_metadata.get(
            "page_number"
        )

        if (
            isinstance(current_page, int)
            and isinstance(next_page, int)
            and current_page != next_page
        ):
            return False

        return True

    @classmethod
    def _group_sections(
        cls,
        sections: list[dict[str, Any]],
        target_words: int,
    ) -> list[list[dict[str, Any]]]:
        """Group compatible adjacent sections up to the target word count."""
        groups: list[list[dict[str, Any]]] = []
        current_group: list[dict[str, Any]] = []
        current_word_count = 0

        for section in sections:
            text = section.get("text", "")

            if (
                not isinstance(text, str)
                or not text.strip()
            ):
                continue

            section_word_count = len(
                text.split()
            )

            if not current_group:
                current_group = [section]
                current_word_count = (
                    section_word_count
                )
                continue

            previous_section = current_group[-1]

            can_group = cls._can_group_sections(
                previous_section,
                section,
            )

            fits_target = (
                current_word_count
                + section_word_count
                <= target_words
            )

            if can_group and fits_target:
                current_group.append(section)
                current_word_count += (
                    section_word_count
                )
            else:
                groups.append(current_group)
                current_group = [section]
                current_word_count = (
                    section_word_count
                )

        if current_group:
            groups.append(current_group)

        return groups

    @classmethod
    def _create_chunks_from_sections(
        cls,
        document_id: str,
        sections: list[dict[str, Any]],
        chunk_size: int,
        overlap: int,
        min_chunk_size: int = 0,
    ) -> list[DocumentChunk]:
        """Create document chunks from processed document sections."""
        groups = cls._group_sections(
            sections=sections,
            target_words=chunk_size,
        )

        chunks: list[DocumentChunk] = []
        chunk_number = 1

        for group in groups:
            group_text_parts: list[str] = []
            source_section_numbers: list[int] = []
            page_numbers: list[int] = []
            group_metadata: dict[str, Any] = {}

            for section in group:
                text = section.get("text", "")

                if (
                    isinstance(text, str)
                    and text.strip()
                ):
                    group_text_parts.append(
                        text.strip()
                    )

                (
                    section_number,
                    section_pages,
                    section_metadata,
                ) = cls._extract_section_provenance(
                    section
                )

                source_section_numbers.append(
                    section_number
                )

                for page_number in section_pages:
                    if (
                        page_number
                        not in page_numbers
                    ):
                        page_numbers.append(
                            page_number
                        )

                group_metadata.update(
                    section_metadata
                )

            group_text = " ".join(
                group_text_parts
            )

            text_chunks = (
                cls._split_text_with_overlap(
                    text=group_text,
                    chunk_size=chunk_size,
                    overlap=overlap,
                    min_chunk_size=min_chunk_size,
                )
            )

            for text_chunk in text_chunks:
                chunk = cls._build_chunk(
                    document_id=document_id,
                    chunk_number=chunk_number,
                    text=text_chunk,
                    source_section_numbers=(
                        source_section_numbers
                    ),
                    page_numbers=page_numbers,
                    metadata=group_metadata,
                )

                chunks.append(chunk)
                chunk_number += 1

        return chunks

    def validate_processed_document(
        self,
        document_id: str,
    ) -> dict[str, Any]:
        try:
            processed_document = (
                self.repository.load_processed_document(
                    document_id
                )
            )
        except DocumentProcessingError as error:
            raise DocumentChunkingError(
                error.message,
                status_code=error.status_code,
                error_code=error.error_code,
            ) from error

        sections = processed_document.get(
            "sections"
        )

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

    def chunk_document(
        self,
        document_id: str,
    ) -> ChunkingResponse:
        """Create retrieval-ready chunks from a processed document."""
        processed_document = (
            self.validate_processed_document(
                document_id
            )
        )

        sections = processed_document["sections"]

        chunks = self._create_chunks_from_sections(
            document_id=document_id,
            sections=sections,
            chunk_size=settings.chunk_size_words,
            overlap=settings.chunk_overlap_words,
            min_chunk_size=(
                settings.min_chunk_size_words
            ),
        )

        if not chunks:
            raise DocumentChunkingError(
                "No chunks could be created from the processed document.",
                status_code=422,
                error_code="NO_CHUNKS_CREATED",
            )

        if (
            len(chunks)
            > settings.max_chunks_per_document
        ):
            raise DocumentChunkingError(
                "Document exceeds the maximum number of allowed chunks.",
                status_code=422,
                error_code="MAX_CHUNKS_EXCEEDED",
            )

        statistics = (
            self._calculate_statistics(chunks)
        )

        output_path = (
            self.chunk_repository.chunks_directory
            / f"{document_id}.json"
        )

        response = ChunkingResponse(
            document_id=document_id,
            status="chunked",
            chunked_at=datetime.now(timezone.utc),
            chunks=chunks,
            statistics=statistics,
            chunks_output_path=str(output_path),
        )

        self.chunk_repository.save_chunks(
            document_id=document_id,
            payload=response.model_dump(
                mode="json"
            ),
        )

        return response

    @staticmethod
    def get_configuration(
    ) -> ChunkingConfigurationResponse:
        return ChunkingConfigurationResponse(
            chunk_size_words=(
                settings.chunk_size_words
            ),
            chunk_overlap_words=(
                settings.chunk_overlap_words
            ),
            min_chunk_size_words=(
                settings.min_chunk_size_words
            ),
            max_chunks_per_document=(
                settings.max_chunks_per_document
            ),
        )


document_chunking_service = (
    DocumentChunkingService(
        repository=document_repository,
        chunk_repository=chunk_repository,
    )
)