from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    chunk_number: int
    text: str
    word_count: int
    character_count: int
    token_estimate: int
    source_section_numbers: list[int] = Field(default_factory=list)
    page_numbers: list[int] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChunkingStatistics(BaseModel):
    chunks_created: int
    total_words: int
    total_characters: int
    average_chunk_words: float
    smallest_chunk_words: int
    largest_chunk_words: int
    configured_chunk_size_words: int
    configured_overlap_words: int


class ChunkingResponse(BaseModel):
    document_id: str
    status: str
    chunked_at: datetime
    chunks: list[DocumentChunk]
    statistics: ChunkingStatistics
    chunks_output_path: str


class ChunkingConfigurationResponse(BaseModel):
    chunk_size_words: int
    chunk_overlap_words: int
    min_chunk_size_words: int
    max_chunks_per_document: int