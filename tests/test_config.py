import os
from unittest.mock import patch

import pytest
from pydantic_core import ValidationError

from nexusmind.config import get_core_config

# Remove global environment variable manipulation.
# These will be handled by fixtures or monkeypatching within each test.
# os.environ["LLM_MODEL_NAME"] = "test-model"
# os.environ["TEMPERATURE"] = "0.5"


def test_initial_config_loading_fails_without_env():
    """
    Ensures that loading the configuration fails as expected
    when no environment variables are provided.
    """
    # Use patch.dict to ensure a completely clean environment for this test
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValidationError):
            get_core_config.cache_clear()
            get_core_config()


def test_default_values():
    """
    Test that the configuration loads default values correctly when
    no environment variables or .env file is present.
    """
    with patch.dict(os.environ, {}, clear=True):
        # We expect a validation error because essential values are missing
        with pytest.raises(ValidationError):
            get_core_config.cache_clear()
            get_core_config()


def test_environment_variable_override(monkeypatch):
    """
    Test that environment variables correctly override the default values.
    """
    get_core_config.cache_clear()
    monkeypatch.setenv("LLM_MODEL_NAME", "test-model-override")
    monkeypatch.setenv("TEMPERATURE", "0.8")
    # Set all other required variables to satisfy validation
    monkeypatch.setenv("OPENAI_API_KEY", "test_key")
    monkeypatch.setenv("STORAGE_BASE_PATH", "/tmp")
    monkeypatch.setenv("CELERY_BROKER_URL", "redis://localhost")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "redis://localhost")
    monkeypatch.setenv("POSTGRES__USER", "test")
    monkeypatch.setenv("POSTGRES__PASSWORD", "test")
    monkeypatch.setenv("POSTGRES__HOST", "db")
    monkeypatch.setenv("POSTGRES__PORT", "5432")
    monkeypatch.setenv("POSTGRES__DB", "testdb")
    monkeypatch.setenv("REDIS__HOST", "redis")
    monkeypatch.setenv("REDIS__PORT", "6379")
    monkeypatch.setenv("REDIS__DB", "1")

    config = get_core_config()
    assert config.llm_model_name == "test-model-override"
    assert config.temperature == 0.8


def test_type_validation(monkeypatch):
    """
    Test that Pydantic raises a validation error for incorrect types.
    """
    get_core_config.cache_clear()
    monkeypatch.setenv("MAX_TOKENS", "not-an-integer")
    # Set all other required variables to satisfy validation
    monkeypatch.setenv("OPENAI_API_KEY", "test_key")
    monkeypatch.setenv("STORAGE_BASE_PATH", "/tmp")
    monkeypatch.setenv("CELERY_BROKER_URL", "redis://localhost")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "redis://localhost")
    monkeypatch.setenv("POSTGRES__USER", "test")
    monkeypatch.setenv("POSTGRES__PASSWORD", "test")
    monkeypatch.setenv("POSTGRES__HOST", "db")
    monkeypatch.setenv("POSTGRES__PORT", "5432")
    monkeypatch.setenv("POSTGRES__DB", "testdb")
    monkeypatch.setenv("REDIS__HOST", "redis")
    monkeypatch.setenv("REDIS__PORT", "6379")
    monkeypatch.setenv("REDIS__DB", "1")

    with pytest.raises(ValidationError):
        get_core_config()


def test_no_env_file_loads_defaults(monkeypatch):
    """
    Test that default values are used when no .env file is specified and
    environment variables are not set for them.
    """
    get_core_config.cache_clear()
    # Set only the required variables, leaving defaults to be tested
    monkeypatch.setenv("OPENAI_API_KEY", "test_key")
    monkeypatch.setenv("STORAGE_BASE_PATH", "/tmp")
    monkeypatch.setenv("CELERY_BROKER_URL", "redis://localhost")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "redis://localhost")
    monkeypatch.setenv("POSTGRES__USER", "test")
    monkeypatch.setenv("POSTGRES__PASSWORD", "test")
    monkeypatch.setenv("POSTGRES__HOST", "db")
    monkeypatch.setenv("POSTGRES__PORT", "5432")
    monkeypatch.setenv("POSTGRES__DB", "testdb")
    monkeypatch.setenv("REDIS__HOST", "redis")
    monkeypatch.setenv("REDIS__PORT", "6379")
    monkeypatch.setenv("REDIS__DB", "1")

    config = get_core_config()
    # These should be the default values from the model definition
    assert config.llm_model_name == "gpt-4o"
    assert config.temperature == 0.7
    assert config.max_tokens == 1000
