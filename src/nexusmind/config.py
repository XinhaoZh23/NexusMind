from functools import lru_cache
from pydantic import Field, validator
from pydantic_settings import SettingsConfigDict, BaseSettings
import os
from typing import Dict, Optional

from .base_config import BaseConfig, MinioConfig, PostgresConfig, RedisConfig


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


@lru_cache()
def get_core_config(app_env: Optional[str] = None) -> CoreConfig:
    """
    Get the core config.

    This function is now a pure function whose output is determined by the
    `app_env` parameter. It is cached with @lru_cache, which works correctly
    because the cache key is now based on the input parameter.
    """
    env_file_name = ".env.prod" if app_env == "production" else ".env"
    
    # Correctly determine the project root, which is three levels up from this file
    # (.../src/nexusmind/config.py -> .../src/nexusmind -> .../src -> PROJECT_ROOT)
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )

    # For tests, the .env files are located in the 'tests' directory
    # For regular execution, they are at the project root
    tests_env_path = os.path.join(project_root, "tests", env_file_name)
    root_env_path = os.path.join(project_root, env_file_name)

    if os.path.exists(tests_env_path):
        env_file_to_load = tests_env_path
    elif os.path.exists(root_env_path):
        env_file_to_load = root_env_path
    else:
        # If no .env file is found (e.g., in CI/CD), Pydantic will rely solely
        # on environment variables, which is the desired behavior.
        env_file_to_load = None

    return CoreConfig(_env_file=env_file_to_load)
