from pydantic_settings import SettingsConfigDict

from core.nexusmind.base_config import BaseConfig


class CoreConfig(BaseConfig):
    """
    Core settings for the application, loaded from environment variables.
    """

    model_config = SettingsConfigDict(extra="ignore")

    # --- LLM Configuration ---
    # The model name to use for language model interactions.
    # This should correspond to a model supported by litellm.
    # Example: "openai/gpt-4", "anthropic/claude-2", "google/gemini-pro"
    llm_model_name: str = "gpt-4o"

    # The temperature for the language model, controlling creativity.
    temperature: float = 0.7

    # The maximum number of tokens to generate in a response.
    max_tokens: int = 1000

    # The API key for OpenAI services, loaded from OPENAI_API_KEY.
    openai_api_key: str | None = None

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

    api_keys: list[str] = []
