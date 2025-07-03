from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    """
    Base configuration class. All other configuration classes should inherit
    from this one.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_nested_delimiter="__", extra="ignore"
    )

    pass


class PostgresConfig(BaseConfig):
    """PostgreSQL configuration."""

    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_name: str = "nexusmind"
    db_echo: bool = False


class RedisConfig(BaseConfig):
    """Redis configuration."""

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0


class MinioConfig(BaseConfig):
    """Minio/S3 configuration."""

    model_config = SettingsConfigDict(env_prefix="MINIO_")
    access_key: str = Field("minioadmin", alias="MINIO_ROOT_USER")
    secret_key: SecretStr = Field("minioadmin", alias="MINIO_ROOT_PASSWORD")
    endpoint: str = "http://localhost:9000"
    bucket: str = "nexusmind"
