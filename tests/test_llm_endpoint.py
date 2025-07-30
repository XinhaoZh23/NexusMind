from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel

from main import app, get_api_key, get_session
from nexusmind.brain.brain import Brain
from nexusmind.database import get_engine

VALID_LLM_API_KEY = "test-llm-api-key"

# This engine will be used across all tests in this module for simplicity
test_engine = get_engine(
    db_url="sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown_module():
    """Create and drop database tables for the entire module."""
    SQLModel.metadata.create_all(test_engine)
    yield
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture(name="client")
def client_fixture():
    """
    Pytest fixture to provide a TestClient with mocked dependencies.
    This is the standard and most robust way to test FastAPI applications.
    """

    def get_session_override():
        with Session(test_engine) as session:
            yield session

    async def get_api_key_override_unauthorized():
        raise HTTPException(status_code=401, detail="Invalid API Key")

    async def get_api_key_override_authorized():
        return VALID_LLM_API_KEY

    # Temporarily override the dependencies for the duration of the test
    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[
        get_api_key
    ] = get_api_key_override_unauthorized  # Default to unauthorized
    yield TestClient(app)

    # Clean up the dependency overrides after the test
    app.dependency_overrides.clear()


def test_unauthorized_access(client: TestClient):
    """
    Test that a request with an invalid API key is correctly rejected.
    The client fixture defaults to an unauthorized state.
    """
    # 1. Prepare test data
    brain = Brain(
        name="Test Brain for Unauthorized",
        llm_model_name="test-model",
        temperature=0.5,
        max_tokens=100,
    )
    brain.save()

    # 2. Make the request and assert
    response = client.post(
        "/chat",
        headers={"X-API-Key": "invalid-api-key"},
        json={"question": "Hello", "brain_id": str(brain.brain_id)},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API Key"


@patch("litellm.completion")
def test_chat_endpoint_success(mock_litellm_completion, client: TestClient):
    """
    Test a successful chat interaction with all dependencies mocked.
    We specifically override the api_key dependency for this single test.
    """
    # 1. Setup Mocks
    async def get_api_key_override_authorized():
        return VALID_LLM_API_KEY

    app.dependency_overrides[get_api_key] = get_api_key_override_authorized

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is a test response."
    mock_litellm_completion.return_value = mock_response

    # 2. Prepare test data
    brain = Brain(
        name="Test Brain for Success",
        llm_model_name="test-model",
        temperature=0.5,
        max_tokens=100,
    )
    brain.save()

    # 3. Make the request and assert
    response = client.post(
        "/chat",
        headers={"X-API-Key": VALID_LLM_API_KEY},
        json={"question": "Hello, world!", "brain_id": str(brain.brain_id)},
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "This is a test response."
    mock_litellm_completion.assert_called_once()
    call_args, call_kwargs = mock_litellm_completion.call_args
    assert call_kwargs["model"] == "test-model"

    # Clean up the specific override for this test
    del app.dependency_overrides[get_api_key]
