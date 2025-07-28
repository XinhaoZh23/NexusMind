from functools import lru_cache
from pydantic import Field, validator
from pydantic_settings import SettingsConfigDict, BaseSettings
import os
from typing import Dict

from .base_config import BaseConfig, MinioConfig, PostgresConfig, RedisConfig

# Module-level cache for CoreConfig instances
_core_config_cache: Dict[str, "CoreConfig"] = {}


class CoreConfig(BaseConfig):
    """
    Core settings for the application, loaded from environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
    )

    # --- LLM Configuration ---
    # The model name to use for language model interactions.
    # This should correspond to a model supported by litellm.
    # Example: "openai/gpt-4", "anthropic/claude-2", "google/gemini-pro"
    llm_model_name: str = Field("gpt-4o", description="Default LLM model name.")

    # The temperature for the language model, controlling creativity.
    temperature: float = Field(0.7, description="LLM temperature.")

    # The maximum number of tokens to generate in a response.
    max_tokens: int = Field(1000, description="LLM max tokens.")

    # The API key for OpenAI services, loaded from OPENAI_API_KEY.
    openai_api_key: str

    # --- S3 Configuration ---
    s3_bucket_name: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = "us-east-1"
    aws_endpoint_url: str | None = None

    # --- Redis Configuration ---

    # --- Storage Configuration ---
    # The base path for local file storage.
    storage_base_path: str

    # Celery settings
    celery_broker_url: str
    celery_result_backend: str
    task_track_started: bool = True

    api_keys: list[str] = []

    postgres: PostgresConfig = Field(default_factory=PostgresConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    minio: MinioConfig | None = Field(default=None)

    @validator("minio", pre=True, always=True)
    def validate_minio(cls, v, values):
        if os.getenv("MINIO_ENDPOINT"):
            return MinioConfig()
        return None


def get_core_config() -> CoreConfig:
    """
    Get the core config.

    This function now checks the APP_ENV environment variable to determine
    which .env file to load, and uses a manual, environment-aware cache
    to avoid reloading configuration unnecessarily.
    """
    env_file = ".env.prod" if os.getenv("APP_ENV") == "production" else ".env"

    if env_file not in _core_config_cache:
        config = CoreConfig(_env_file=env_file)
        _core_config_cache[env_file] = config

    return _core_config_cache[env_file]
