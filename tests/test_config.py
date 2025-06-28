import os
import pytest
from pydantic import ValidationError

# 在导入CoreConfig之前设置环境变量，以测试覆盖
os.environ["LLM_MODEL_NAME"] = "test-model"
os.environ["TEMPERATURE"] = "0.5"

from core.nexusmind.config import CoreConfig


def test_default_values():
    """
    Test that the default values are loaded correctly when no environment variables are set.
    We need to temporarily unset env vars for this test.
    """
    original_llm_model_name = os.environ.pop("LLM_MODEL_NAME", None)
    original_temperature = os.environ.pop("TEMPERATURE", None)
    original_max_tokens = os.environ.pop("MAX_TOKENS", None)

    try:
        config = CoreConfig()
        # Unset MAX_TOKENS which was not set at the top level
        assert config.max_tokens == 1000
    finally:
        # Restore environment variables
        if original_llm_model_name is not None:
            os.environ["LLM_MODEL_NAME"] = original_llm_model_name
        if original_temperature is not None:
            os.environ["TEMPERATURE"] = original_temperature
        if original_max_tokens is not None:
            os.environ["MAX_TOKENS"] = original_max_tokens


def test_environment_variable_override():
    """
    Test that environment variables correctly override the default values.
    """
    config = CoreConfig()
    assert config.llm_model_name == "test-model"
    assert config.temperature == 0.5


def test_type_validation():
    """
    Test that Pydantic raises a validation error for incorrect types.
    """
    os.environ["MAX_TOKENS"] = "not-an-integer"
    with pytest.raises(ValidationError):
        CoreConfig()
    # Clean up the invalid environment variable
    del os.environ["MAX_TOKENS"]

# Edge case test for init without env var overrides to ensure defaults are applied
def test_init_without_override():
    """
    Test initialization without any overrides to ensure default values are used.
    """
    # Temporarily remove env vars that might affect this test
    original_model = os.environ.pop('LLM_MODEL_NAME', None)
    original_temp = os.environ.pop('TEMPERATURE', None)
    original_tokens = os.environ.pop('MAX_TOKENS', None)

    try:
        config = CoreConfig()
        assert config.llm_model_name == "gpt-4o"
        assert config.temperature == 0.0
        assert config.max_tokens == 1000
    finally:
        # Restore env vars
        if original_model is not None:
            os.environ['LLM_MODEL_NAME'] = original_model
        if original_temp is not None:
            os.environ['TEMPERATURE'] = original_temp
        if original_tokens is not None:
            os.environ['MAX_TOKENS'] = original_tokens 