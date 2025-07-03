import os
from functools import lru_cache
from pydantic_settings import SettingsConfigDict
from pydantic import Field

from .base_config import BaseConfig, MinioConfig, PostgresConfig, RedisConfig


class CoreConfig(BaseConfig):
    """
    Core settings for the application, loaded from environment variables.
    """

    model_config = SettingsConfigDict(extra="ignore")

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
    openai_api_key: str = "sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

    # --- Database Configuration ---
    database_url: str = "postgresql://user:password@localhost:5432/nexusmind_db"

    # --- S3 Configuration ---
    s3_bucket_name: str = "nexusmind-document-storage"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = "us-east-1"
    aws_endpoint_url: str | None = None

    # --- Redis Configuration ---
    redis_url: str = "redis://localhost:6379/0"

    # --- Storage Configuration ---
    # The base path for local file storage.
    storage_base_path: str = "storage"

    # Celery settings
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    task_track_started: bool = True

    api_keys: list[str] = []

    postgres: PostgresConfig = PostgresConfig()
    redis: RedisConfig = RedisConfig()
    minio: MinioConfig = MinioConfig()


def get_core_config() -> CoreConfig:
    """
    Get the core config, cached to avoid multiple loads.
    """
    return CoreConfig()
