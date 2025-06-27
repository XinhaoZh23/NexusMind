from pydantic_settings import BaseSettings


class BaseConfig(BaseSettings):
    """
    Base configuration class. All other configuration classes should inherit from this one.
    """

    pass

