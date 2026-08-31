from functools import lru_cache
from pathlib import Path

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "KnowFlow AI"
    app_version: str = "0.4.0"
    app_description: str = (
        "Enterprise knowledge assistant powered by retrieval-augmented generation."
    )

    environment: str = "development"
    debug: bool = True

    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"

    upload_directory: Path = PROJECT_ROOT / "documents"
    processed_directory: Path = PROJECT_ROOT / "documents" / "processed"
    chunks_directory: Path = PROJECT_ROOT / "documents" / "chunks"

    max_upload_size_mb: int = 10
    upload_chunk_size_bytes: int = 1024 * 1024
    max_extracted_characters: int = 5_000_000

    chunk_size_words: int = 180
    chunk_overlap_words: int = 30
    min_chunk_size_words: int = 40
    max_chunks_per_document: int = 10_000

    allowed_document_extensions: tuple[str, ...] = (
        ".pdf",
        ".docx",
        ".txt",
    )

    allowed_document_mime_types: tuple[str, ...] = (
        "application/pdf",
        (
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
        "text/plain",
        "application/octet-stream",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator(
        "max_upload_size_mb",
        "upload_chunk_size_bytes",
        "max_extracted_characters",
        "chunk_size_words",
        "min_chunk_size_words",
        "max_chunks_per_document",
    )
    @classmethod
    def validate_positive_integer(cls, value: int) -> int:
        if value <= 0:
            raise ValueError(
                "Numeric application settings must be greater than zero"
            )

        return value

    @field_validator("chunk_overlap_words")
    @classmethod
    def validate_non_negative_integer(cls, value: int) -> int:
        if value < 0:
            raise ValueError(
                "CHUNK_OVERLAP_WORDS cannot be negative"
            )

        return value

    @model_validator(mode="after")
    def validate_chunking_configuration(self) -> "Settings":
        if self.chunk_overlap_words >= self.chunk_size_words:
            raise ValueError(
                "CHUNK_OVERLAP_WORDS must be smaller than CHUNK_SIZE_WORDS"
            )

        if self.min_chunk_size_words > self.chunk_size_words:
            raise ValueError(
                "MIN_CHUNK_SIZE_WORDS cannot exceed CHUNK_SIZE_WORDS"
            )

        return self

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()