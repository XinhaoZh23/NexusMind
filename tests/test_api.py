import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import uuid
import time
import os
from pathlib import Path

# Add project root to path to allow imports
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import app, get_processor_registry, get_s3_storage, get_core_config
from core.nexusmind.celery_app import app as celery_app

# Create a TestClient instance
client = TestClient(app)

# --- Test Fixtures ---
VALID_API_KEY = "test-key"

@pytest.fixture
def settings(monkeypatch):
    """Fixture to set environment variables and configure Celery for testing."""
    monkeypatch.setenv("API_KEYS", f'["{VALID_API_KEY}"]')
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "minioadmin")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "minioadmin")
    monkeypatch.setenv("AWS_ENDPOINT_URL", "http://localhost:9000")
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")

    # Force Celery to run tasks eagerly (synchronously) and store results in tests
    celery_app.conf.update(
        task_always_eager=True,
        task_store_eager_result=True,
    )
    
    # Pydantic settings are cached, clear the cache to force reload
    get_core_config.cache_clear()
    yield
    # Clear cache again after test to avoid side effects
    get_core_config.cache_clear()

# --- Test Data ---
@pytest.fixture
def test_txt_content() -> str:
    return "The sky is blue and the grass is green."

@pytest.fixture
def mock_embedding() -> list[float]:
    # A 1536-dimensional vector of 0.1s, similar to text-embedding-ada-002
    return [0.1] * 1536

# --- E2E API Test ---
@patch('core.nexusmind.llm.llm_endpoint.litellm.completion')
@patch('core.nexusmind.llm.llm_endpoint.litellm.embedding')
def test_async_upload_and_chat(mock_embedding_call, mock_completion_call, test_txt_content, mock_embedding, settings):
    """
    Tests the full end-to-end flow in a synchronous testing environment.
    1. Upload a file, which is processed immediately due to Celery's eager mode.
    2. Ask a question about the file.
    3. Verify the response.
    """
    # --- Mock external services ---
    mock_embedding_response = MagicMock()
    mock_embedding_response.data = [MagicMock()]
    mock_embedding_response.data[0].embedding = mock_embedding
    mock_embedding_call.return_value = mock_embedding_response

    mock_completion_response = MagicMock()
    mock_completion_response.choices[0].message.content = "The sky is indeed blue."
    mock_completion_call.return_value = mock_completion_response
    
    headers = {"X-API-Key": VALID_API_KEY}

    # --- 1. Upload the file (should be processed synchronously) ---
    brain_id = str(uuid.uuid4())
    files = {"file": ("test_doc.txt", test_txt_content.encode('utf-8'), "text/plain")}
    response_upload = client.post(
        "/upload", 
        data={"brain_id": brain_id}, 
        files=files,
        headers=headers
    )

    # Assert upload was accepted and processed
    assert response_upload.status_code == 200
    response_json = response_upload.json()
    assert "task_id" in response_json
    task_id = response_json["task_id"]

    # --- 2. Verify task status is SUCCESS directly ---
    response_status = client.get(f"/upload/status/{task_id}")
    assert response_status.status_code == 200
    status_json = response_status.json()
    assert status_json.get("status") == "SUCCESS"

    # --- 3. Chat about the file ---
    response_chat = client.post(
        "/chat",
        json={"brain_id": brain_id, "question": "What color is the sky?"},
        headers=headers
    )

    # Assert chat was successful
    assert response_chat.status_code == 200
    assert "The sky is indeed blue." in response_chat.json()["answer"]

    # --- 4. Verify mocks were called ---
    mock_embedding_call.assert_called()
    mock_completion_call.assert_called()

    completion_args, completion_kwargs = mock_completion_call.call_args
    prompt_messages = completion_kwargs.get("messages", [])
    assert len(prompt_messages) > 0
    final_prompt = prompt_messages[0].get("content", "")
    assert "the grass is green" in final_prompt.lower()

def test_chat_without_api_key(settings):
    """Test that a request without an API key is rejected."""
    response = client.post(
        "/chat",
        json={"brain_id": str(uuid.uuid4()), "question": "test"}
    )
    assert response.status_code == 403
    assert "Not authenticated" in response.text

def test_chat_with_invalid_api_key(settings):
    """Test that a request with an invalid API key is rejected."""
    response = client.post(
        "/chat",
        json={"brain_id": str(uuid.uuid4()), "question": "test"},
        headers={"X-API-Key": "invalid-key"}
    )
    assert response.status_code == 403
    assert "Could not validate credentials" in response.text 