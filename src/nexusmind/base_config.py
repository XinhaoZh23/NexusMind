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

    aws_access_key_id: str = "minioadmin"
    aws_secret_access_key: str = "minioadmin"
    aws_endpoint_url: str = "http://localhost:9000"
    s3_bucket_name: str = "nexusmind-documents"
