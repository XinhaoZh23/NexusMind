from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from nexusmind.config import CoreConfig, get_core_config


def get_test_llm_config():
    """Returns a CoreConfig instance for testing the LLM endpoint."""
    return CoreConfig(llm_model_name="test-model", temperature=0.5, max_tokens=150)


@pytest.fixture
def client():
    """
    Pytest fixture to provide a TestClient with dependency overrides.
    This ensures that each test gets a client with the correct configuration
    for the LLM endpoint tests.
    """
    app.dependency_overrides[get_core_config] = get_test_llm_config
    yield TestClient(app)
    # Clean up the dependency overrides after the test
    app.dependency_overrides.clear()


def test_unauthorized_access(client: TestClient):
    """
    Test that a request without a valid API key is rejected.
    """
    response = client.post(
        "/chat",
        headers={"X-API-Key": "invalid-api-key"},
        json={"text": "Hello"},
    )
    assert response.status_code == 401
    assert "Invalid API Key" in response.text


@patch("litellm.completion")
def test_chat_endpoint_success(mock_litellm_completion, client: TestClient):
    """Test the /chat endpoint for a successful interaction."""
    # Mock the response from litellm
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is a test response."
    mock_litellm_completion.return_value = mock_response

    # Test with a valid API key from the overridden config
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
