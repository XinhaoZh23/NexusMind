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

from main import app, get_processor_registry, get_storage, get_core_config

# Create a TestClient instance
client = TestClient(app)

# --- Test Fixtures ---
VALID_API_KEY = "test-key"

@pytest.fixture
def settings(tmp_path):
    """Fixture to create a .env file for testing."""
    # Pydantic v2 expects a JSON-formatted string for lists from env vars.
    env_content = f'API_KEYS=\'[\"{VALID_API_KEY}\"]\''
    env_file = tmp_path / ".env"
    env_file.write_text(env_content)
    
    # Pydantic settings are cached, clear the cache to force reload
    get_core_config.cache_clear()
    
    # Change CWD for the duration of the test
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield
    os.chdir(original_cwd)
    # Clear cache again after test
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
    Tests the full asynchronous end-to-end flow with a valid API key.
    1. Upload a file, get a task_id.
    2. Poll the status endpoint until the task is successful.
    3. Ask a question about the file.
    4. Verify the response.
    """
    # --- Mock external services ---
    mock_embedding_response = MagicMock()
    # Handle the case where the mock might be called with a list of texts
    mock_embedding_response.data = [MagicMock()]
    mock_embedding_response.data[0].embedding = mock_embedding
    mock_embedding_call.return_value = mock_embedding_response

    mock_completion_response = MagicMock()
    mock_completion_response.choices[0].message.content = "The sky is indeed blue."
    mock_completion_call.return_value = mock_completion_response
    
    headers = {"X-API-Key": VALID_API_KEY}

    # --- 1. Upload the file and start background task ---
    brain_id = str(uuid.uuid4())
    files = {"file": ("test_doc.txt", test_txt_content.encode('utf-8'), "text/plain")}
    response_upload = client.post(
        "/upload", 
        data={"brain_id": brain_id}, 
        files=files,
        headers=headers
    )

    # Assert upload was accepted
    assert response_upload.status_code == 202
    response_json = response_upload.json()
    assert "task_id" in response_json
    task_id = response_json["task_id"]

    # --- 2. Poll for task completion ---
    max_wait = 10  # seconds
    start_time = time.time()
    final_status = ""
    while time.time() - start_time < max_wait:
        response_status = client.get(f"/upload/status/{task_id}")
        assert response_status.status_code == 200
        status_json = response_status.json()
        final_status = status_json.get("status")
        if final_status == "SUCCESS":
            break
        assert final_status in ["PENDING", "PROCESSING"]
        time.sleep(0.1)

    assert final_status == "SUCCESS", f"Task did not succeed within {max_wait} seconds."

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