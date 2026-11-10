from functools import lru_cache

from pydantic import BaseModel, Field


class Settings(BaseModel):
    environment: str = Field(default="development", alias="CONSULTAI_ENV")
    database_url: str = Field(
        default="postgresql://consultai:consultai@localhost:5432/consultai",
        alias="CONSULTAI_DATABASE_URL",
    )
    ollama_base_url: str = Field(default="http://localhost:11434", alias="CONSULTAI_OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3.2", alias="CONSULTAI_OLLAMA_MODEL")
    external_llm_enabled: bool = Field(default=False, alias="CONSULTAI_EXTERNAL_LLM_ENABLED")
    retention_days: int = Field(default=30, ge=1, alias="CONSULTAI_RETENTION_DAYS")

    model_config = {"populate_by_name": True}


@lru_cache
def get_settings() -> Settings:
    import os

    values = {key: value for key, value in os.environ.items() if key.startswith("CONSULTAI_")}
    return Settings.model_validate(values)
