from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel

from main import app, get_api_key
from nexusmind.brain.brain import Brain
from nexusmind.database import get_engine, get_session

VALID_LLM_API_KEY = "test-llm-api-key"

# Create a test engine for the LLM endpoint tests
test_engine = get_engine(
    db_url="sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture
def client():
    """
    Pytest fixture to provide a TestClient with overrides for both
    API key security dependency and database session dependency.
    This ensures complete isolation for testing protected endpoints.
    """
    # Create tables in the test database
    SQLModel.metadata.create_all(test_engine)

    # Create a session for the test
    test_session = Session(test_engine)

    def get_test_session():
        """Override for get_session dependency to use test database."""
        return test_session

    # Override both the API key and database session dependencies
    app.dependency_overrides[get_api_key] = lambda: VALID_LLM_API_KEY
    app.dependency_overrides[get_session] = get_test_session

    yield TestClient(app)

    # Clean up the dependency overrides after the test
    app.dependency_overrides.clear()

    # Close the test session and drop tables after the test
    test_session.close()
    SQLModel.metadata.drop_all(test_engine)


def test_unauthorized_access(client: TestClient):
    """
    Test that a request without a valid API key is rejected.
    """
    # Create a dummy brain for the test
    brain = Brain(
        name="Test Brain for Unauthorized",
        llm_model_name="test-model",
        temperature=0.5,
        max_tokens=100,
    )
    brain.save()

    response = client.post(
        "/chat",
        headers={"X-API-Key": "invalid-api-key"},
        json={"question": "Hello", "brain_id": str(brain.brain_id)},
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

    # Create a dummy brain for the test
    brain = Brain(
        name="Test Brain for Success",
        llm_model_name="test-model",
        temperature=0.5,
        max_tokens=100,
    )
    brain.save()

    # Test with a valid API key from the overridden config
    response = client.post(
        "/chat",
        headers={"X-API-Key": VALID_LLM_API_KEY},
        json={"question": "Hello, world!", "brain_id": str(brain.brain_id)},
    )

    assert response.status_code == 200
    assert response.json()["response"] == "This is a test response."
    mock_litellm_completion.assert_called_once()
    call_args, call_kwargs = mock_litellm_completion.call_args
    assert call_kwargs["model"] == "test-model"
    assert call_kwargs["messages"] == [{"role": "user", "content": "Hello, world!"}]
    assert call_kwargs["temperature"] == 0.5
    assert call_kwargs["max_tokens"] == 150
