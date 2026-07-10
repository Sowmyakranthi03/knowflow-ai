from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    document_id: str = Field(
        description="Unique identifier assigned to the uploaded document."
    )
    original_filename: str = Field(
        description="Original filename supplied by the client."
    )
    stored_filename: str = Field(
        description="Generated safe filename used by the server."
    )
    file_extension: str
    content_type: str
    size_bytes: int
    size_mb: float
    uploaded_at: datetime
    status: str = "uploaded"


class SupportedDocumentTypesResponse(BaseModel):
    extensions: list[str]
    max_upload_size_mb: int


class ExtractedSection(BaseModel):
    section_number: int
    section_type: str
    text: str
    character_count: int
    word_count: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentStatistics(BaseModel):
    section_count: int
    page_count: int | None = None
    paragraph_count: int | None = None
    table_count: int | None = None
    character_count: int
    word_count: int
    empty_section_count: int


class DocumentProcessingResponse(BaseModel):
    document_id: str
    stored_filename: str
    file_extension: str
    parser: str
    status: str
    processed_at: datetime
    full_text: str
    sections: list[ExtractedSection]
    statistics: DocumentStatistics
    processed_output_path: str