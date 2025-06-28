import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import uuid

# Add project root to path to allow imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import app, get_processor_registry, get_storage

# Create a TestClient instance
client = TestClient(app)

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
def test_upload_and_chat_e2e(mock_embedding_call, mock_completion_call, test_txt_content, mock_embedding):
    """
    Tests the full end-to-end flow:
    1. Upload a file.
    2. Ask a question about the file.
    3. Verify the response.
    """
    # --- Mock external services ---
    # Mock the embedding call
    mock_embedding_response = MagicMock()
    mock_embedding_response.data[0].embedding = mock_embedding
    mock_embedding_call.return_value = mock_embedding_response

    # Mock the completion call
    mock_completion_response = MagicMock()
    mock_completion_response.choices[0].message.content = "The sky is indeed blue."
    mock_completion_call.return_value = mock_completion_response
    
    # --- 1. Upload the file ---
    brain_id = str(uuid.uuid4())
    files = {"file": ("test_doc.txt", test_txt_content.encode('utf-8'), "text/plain")}
    response_upload = client.post(
        "/upload", 
        data={"brain_id": brain_id}, 
        files=files
    )

    # Assert upload was successful
    assert response_upload.status_code == 200
    assert "uploaded and processed successfully" in response_upload.json()["message"]

    # --- 2. Chat about the file ---
    response_chat = client.post(
        "/chat",
        json={"brain_id": brain_id, "question": "What color is the sky?"}
    )

    # Assert chat was successful
    assert response_chat.status_code == 200
    assert "The sky is indeed blue." in response_chat.json()["answer"]

    # --- 3. Verify mocks were called ---
    # Verify that the content was embedded
    mock_embedding_call.assert_called()
    # Verify that the LLM was called to generate an answer
    mock_completion_call.assert_called()

    # Verify that the context from the document was included in the prompt
    completion_args, completion_kwargs = mock_completion_call.call_args
    prompt_messages = completion_kwargs.get("messages", [])
    assert len(prompt_messages) > 0
    final_prompt = prompt_messages[0].get("content", "")
    assert "the grass is green" in final_prompt.lower() 