from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "KnowFlow AI"
    app_version: str = "0.1.0"
    app_description: str = (
        "Enterprise knowledge assistant powered by retrieval-augmented generation."
    )

    environment: str = "development"
    debug: bool = True

    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()