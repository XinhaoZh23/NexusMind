from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    """
    Base configuration class. All other configuration classes should inherit
    from this one.
    """

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    pass


class PostgresConfig(BaseConfig):
    """PostgreSQL configuration."""

    model_config = SettingsConfigDict(env_prefix="POSTGRES_")
    user: str
    password: SecretStr
    host: str
    port: int
    db: str

    def get_db_url(self) -> str:
        return (
            f"postgresql://{self.user}:{self.password.get_secret_value()}"
            f"@{self.host}:{self.port}/{self.db}"
        )


class RedisConfig(BaseConfig):
    """Redis configuration."""

    redis_host: str
    redis_port: int
    redis_db: int


class MinioConfig(BaseConfig):
    """Minio/S3 configuration."""

    model_config = SettingsConfigDict(env_prefix="MINIO_")
    access_key: str = Field(alias="MINIO_ROOT_USER")
    secret_key: SecretStr = Field(alias="MINIO_ROOT_PASSWORD")
    endpoint: str
    bucket: str
