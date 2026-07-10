from datetime import datetime

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