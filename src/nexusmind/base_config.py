from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    """
    Base configuration class. All other configuration classes should inherit
    from this one.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    pass


class PostgresConfig(BaseConfig):
    """PostgreSQL configuration."""

    model_config = SettingsConfigDict(env_prefix="POSTGRES_")
    user: str = "nexusmind_user"
    password: SecretStr = "nexusmind_password"
    host: str = "localhost"
    port: int = 5432
    db: str = "nexusmind_db"

    def get_db_url(self) -> str:
        return (
            f"postgresql://{self.user}:{self.password.get_secret_value()}"
            f"@{self.host}:{self.port}/{self.db}"
        )


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
