import uuid
import os
import boto3
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

from nexusmind.celery_app import app as celery_app
from main import app, get_core_config
from nexusmind.storage.s3_storage import S3Storage, get_s3_storage
from nexusmind.base_config import MinioConfig


@pytest.fixture
def api_client(settings) -> TestClient:
    """
    Provides a TestClient instance for API testing with mocked S3.
    This fixture handles S3 mocking and dependency overrides.
    """
    with mock_aws():
        # 1. Create a mock S3 client
        s3_client = boto3.client("s3", region_name="us-east-1")

        # 2. Define the dependency override
        def get_mock_s3_storage():
            config = get_core_config().minio
            # Ensure the bucket exists in the mock environment
            s3_client.create_bucket(Bucket=config.bucket)
            # Inject the mock client
            return S3Storage(config=config, s3_client=s3_client)

        # 3. Apply the override
        app.dependency_overrides[get_s3_storage] = get_mock_s3_storage

        with TestClient(app) as client:
            yield client

        # 4. Clean up the override
        app.dependency_overrides.clear()


# --- Test Fixtures ---
VALID_API_KEY = "test-key"


@pytest.fixture
def settings(monkeypatch):
    """Fixture to set environment variables and configure Celery for testing."""
    monkeypatch.setenv("API_KEYS", f'["{VALID_API_KEY}"]')
    # Ensure the endpoint is not set, so moto can mock S3
    monkeypatch.delenv("AWS_ENDPOINT_URL", raising=False)
    # Use dummy credentials for moto as per best practice
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
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


@pytest.fixture
def test_txt_content() -> str:
    return "The sky is blue and the grass is green."


@pytest.fixture
def mock_embedding() -> list[float]:
    # A 1536-dimensional vector of 0.1s, similar to text-embedding-ada-002
    return [0.1] * 1536


# --- E2E API Test ---
@patch("nexusmind.llm.llm_endpoint.litellm.completion")
@patch("nexusmind.llm.llm_endpoint.litellm.embedding")
def test_async_upload_and_chat(
    mock_embedding_call,
    mock_completion_call,
    test_txt_content,
    mock_embedding,
    api_client,  # Note: settings is now used by api_client
):
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
    files = {"file": ("test_doc.txt", test_txt_content.encode("utf-8"), "text/plain")}
    response_upload = api_client.post(
        "/upload", data={"brain_id": brain_id}, files=files, headers=headers
    )

    # Assert upload was accepted and processed
    assert response_upload.status_code == 200
    response_json = response_upload.json()
    assert "task_id" in response_json
    task_id = response_json["task_id"]

    # --- 2. Verify task status is SUCCESS directly ---
    response_status = api_client.get(f"/upload/status/{task_id}")
    assert response_status.status_code == 200
    status_json = response_status.json()
    assert status_json.get("status") == "SUCCESS"

    # --- 3. Chat about the file ---
    response_chat = api_client.post(
        "/chat",
        json={"brain_id": brain_id, "question": "What color is the sky?"},
        headers=headers,
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


def test_chat_without_api_key(settings, api_client):
    """Test that a request without an API key is rejected."""
    response = api_client.post(
        "/chat", json={"brain_id": str(uuid.uuid4()), "question": "test"}
    )
    assert response.status_code == 403
    assert "Not authenticated" in response.text


def test_chat_with_invalid_api_key(settings, api_client):
    """Test that a request with an invalid API key is rejected."""
    response = api_client.post(
        "/chat",
        json={"brain_id": str(uuid.uuid4()), "question": "test"},
        headers={"X-API-Key": "invalid-key"},
    )
    assert response.status_code == 403
    assert "Could not validate credentials" in response.text
