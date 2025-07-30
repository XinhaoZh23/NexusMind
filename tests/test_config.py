import os  # noqa
from unittest.mock import patch  # noqa

import pytest
from pydantic_core import ValidationError

from nexusmind.config import CoreConfig

# Remove global environment variable manipulation.
# These will be handled by fixtures or monkeypatching within each test.
# os.environ["LLM_MODEL_NAME"] = "test-model"
# os.environ["TEMPERATURE"] = "0.5"


def test_core_config_loads_from_env():
    """
    Tests if the CoreConfig successfully loads settings from the environment.
    This relies on the `mock_env` fixture in conftest.py to set the variables.
    """
    config = CoreConfig()

    assert config.llm_model_name == "gpt-4o"  # Default value
    assert config.openai_api_key == "test_openai_api_key"
    assert config.postgres.user == "testuser"
    assert config.postgres.password.get_secret_value() == "testpassword"
    assert config.redis.redis_host == "localhost"
    assert config.redis.redis_db == 1
    assert config.minio.access_key == "testminiouser"
    assert config.minio.secret_key.get_secret_value() == "testminiopassword"


def test_core_config_missing_required_field_fails(monkeypatch):
    """
    Tests that validation fails if a required field is missing.
    We explicitly remove a required variable to test this.
    """
    monkeypatch.delenv("POSTGRES_USER")

    with pytest.raises(ValidationError) as exc_info:
        CoreConfig()

    # Pydantic v2 provides structured errors. We check for the specific error.
    errors = exc_info.value.errors()
    assert len(errors) > 0
    # Check that the error is for the 'user' field within PostgresConfig
    assert "PostgresConfig" in str(exc_info.value)
    assert errors[0]["loc"] == ("user",)
    assert errors[0]["type"] == "missing"
