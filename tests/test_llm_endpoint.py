import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel

from main import app
from nexusmind.brain.brain import Brain
from nexusmind.database import get_engine

VALID_LLM_API_KEY = "test-llm-api-key"

# This engine will be used across all tests in this module for simplicity
test_engine = get_engine(
    db_url="sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def setup_module(module):
    """Create database tables before any tests in this module run."""
    SQLModel.metadata.create_all(test_engine)


def teardown_module(module):
    """Drop database tables after all tests in this module have run."""
    SQLModel.metadata.drop_all(test_engine)


@patch("main.get_session")
@patch("main.get_api_key", new_callable=AsyncMock)
def test_unauthorized_access(mock_get_api_key, mock_get_session):
    """
    Test that a request with an invalid API key is correctly rejected.
    """
    # 1. Setup Mocks for an async function
    # The side_effect needs to be a callable that returns the exception
    mock_get_api_key.side_effect = HTTPException(
        status_code=401, detail="Invalid API Key"
    )

    # Even though it's an auth test, the session dependency still needs to be mocked
    with Session(test_engine) as session:
        mock_get_session.return_value = session

        # 2. Create TestClient inside the patched context
        client = TestClient(app)

        # 3. Prepare test data
        brain = Brain(
            name="Test Brain for Unauthorized",
            llm_model_name="test-model",
            temperature=0.5,
            max_tokens=100,
        )
        brain.save()

        # 4. Make the request and assert
        response = client.post(
            "/chat",
            headers={"X-API-Key": "invalid-api-key"},
            json={"question": "Hello", "brain_id": str(brain.brain_id)},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid API Key"


@patch("litellm.completion")
@patch("main.get_session")
@patch("main.get_api_key", new_callable=AsyncMock)
def test_chat_endpoint_success(
    mock_get_api_key, mock_get_session, mock_litellm_completion
):
    """
    Test a successful chat interaction with all dependencies mocked.
    """
    # 1. Setup Mocks for async and sync functions
    mock_get_api_key.return_value = VALID_LLM_API_KEY

    with Session(test_engine) as session:
        mock_get_session.return_value = session

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is a test response."
        mock_litellm_completion.return_value = mock_response

        # 2. Create TestClient inside the patched context
        client = TestClient(app)

        # 3. Prepare test data
        brain = Brain(
            name="Test Brain for Success",
            llm_model_name="test-model",
            temperature=0.5,
            max_tokens=100,
        )
        brain.save()

        # 4. Make the request and assert
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
        # Note: The actual call to the LLM now happens inside NexusRAG,
        # so we are not asserting the exact messages/temperature/max_tokens here,
        # as that would be testing the implementation of NexusRAG, not the endpoint.
        # This keeps the endpoint test focused on its own logic.
