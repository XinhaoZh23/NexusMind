from pydantic import BaseModel, Field, SecretStr  # noqa
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


class PostgresConfig(BaseModel):
    """PostgreSQL configuration."""

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


class RedisConfig(BaseModel):
    """Redis configuration."""

    host: str
    port: int
    db: int


class MinioConfig(BaseModel):
    """Minio/S3 configuration."""

    access_key: str
    secret_key: SecretStr
    endpoint: str
    bucket: str
