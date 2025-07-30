from unittest.mock import MagicMock, patch

import pytest  # noqa
from fastapi.testclient import TestClient

from main import app
from nexusmind.config import CoreConfig, get_core_config

# This client will be used for endpoint tests
client = TestClient(app)


def get_test_llm_config():
    """Returns a CoreConfig instance for testing the LLM endpoint."""
    # The `mock_env` fixture in conftest ensures all necessary env vars are set.
    # Therefore, we can now instantiate CoreConfig directly without special
    # parameters like `_env_file=None`.
    return CoreConfig(llm_model_name="test-model", temperature=0.5, max_tokens=150)


# Override the dependency for the duration of the tests in this module
app.dependency_overrides[get_core_config] = get_test_llm_config


def test_unauthorized_access():
    """
    Test that a request without a valid API key is rejected.
    The `mock_env` fixture provides a default set of keys, so we test against
    a key that is not in that set.
    """
    response = client.post(
        "/chat",
        headers={"X-API-Key": "invalid-api-key"},
        json={"text": "Hello"},
    )
    assert response.status_code == 401
    assert "Invalid API Key" in response.text


@patch("litellm.completion")
def test_chat_endpoint_success(mock_litellm_completion):
    """Test the /chat endpoint for a successful interaction."""
    # Mock the response from litellm
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is a test response."
    mock_litellm_completion.return_value = mock_response

    # Test with a valid API key, which is now set by the conftest.py mock_env
    api_key = get_test_llm_config().api_keys[0]
    response = client.post(
        "/chat",
        headers={"X-API-Key": f"{api_key}"},
        json={"text": "Hello, world!"},
    )

    assert response.status_code == 200
    assert response.json()["response"] == "This is a test response."
    mock_litellm_completion.assert_called_once()
    call_args, call_kwargs = mock_litellm_completion.call_args
    assert call_kwargs["model"] == "test-model"
    assert call_kwargs["messages"] == [{"role": "user", "content": "Hello, world!"}]
    assert call_kwargs["temperature"] == 0.5
    assert call_kwargs["max_tokens"] == 150
