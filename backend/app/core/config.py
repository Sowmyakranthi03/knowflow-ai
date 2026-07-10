from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "KnowFlow AI"
    app_version: str = "0.3.0"
    app_description: str = (
        "Enterprise knowledge assistant powered by retrieval-augmented generation."
    )

    environment: str = "development"
    debug: bool = True

    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"

    upload_directory: Path = PROJECT_ROOT / "documents"
    processed_directory: Path = PROJECT_ROOT / "documents" / "processed"

    max_upload_size_mb: int = 10
    upload_chunk_size_bytes: int = 1024 * 1024
    max_extracted_characters: int = 5_000_000

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
    )
    @classmethod
    def validate_positive_integer(cls, value: int) -> int:
        if value <= 0:
            raise ValueError(
                "Numeric processing settings must be greater than zero"
            )

        return value

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()