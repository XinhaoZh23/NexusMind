from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app, get_api_key

VALID_LLM_API_KEY = "test-llm-api-key"


@pytest.fixture
def client():
    """
    Pytest fixture to provide a TestClient with a direct override for the
    API key security dependency. This is the most robust way to test
    protected endpoints.
    """
    app.dependency_overrides[get_api_key] = lambda: VALID_LLM_API_KEY
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
    response = client.post(
        "/chat",
        headers={"X-API-Key": VALID_LLM_API_KEY},
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
