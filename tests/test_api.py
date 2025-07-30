import os
import uuid
from unittest.mock import MagicMock, patch, create_autospec

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws
from pydantic import SecretStr
from sqlmodel import Session, SQLModel, create_engine

from main import app, get_core_config
from nexusmind.base_config import MinioConfig, PostgresConfig, RedisConfig
from nexusmind.celery_app import app as celery_app
from nexusmind.config import CoreConfig
from nexusmind.database import get_session
from nexusmind.processor.splitter import Chunk
from nexusmind.storage.s3_storage import S3Storage, get_s3_storage

VALID_API_KEY = "test-key"

# This engine will be used for all tests.
# The `connect_args={"check_same_thread": False}` is a specific requirement for using SQLite with FastAPI.
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
)


@pytest.fixture(name="session")
def session_fixture():
    """
    Creates a new database session for each test.
    This fixture NO LONGER handles table creation/deletion.
    """
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session, monkeypatch: pytest.MonkeyPatch):
    """
    Provides a TestClient that uses the in-memory SQLite database.
    This fixture now handles the entire lifecycle of the test database tables.
    """
    # Create tables before the test runs
    SQLModel.metadata.create_all(engine)

    def get_session_override():
        return session

    # 1. Set environment variables for testing
    monkeypatch.setenv("API_KEYS", f'["{VALID_API_KEY}"]')
    monkeypatch.delenv("AWS_ENDPOINT_URL", raising=False)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")

    # The database variables are no longer needed as we are using SQLite in-memory
    monkeypatch.delenv("POSTGRES_HOST", raising=False)
    monkeypatch.delenv("POSTGRES_USER", raising=False)
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)
    monkeypatch.delenv("POSTGRES_DB", raising=False)
    monkeypatch.delenv("POSTGRES_PORT", raising=False)

    # Redis variables are not used in API tests, can be removed
    monkeypatch.delenv("REDIS_HOST", raising=False)
    monkeypatch.delenv("REDIS_PORT", raising=False)
    monkeypatch.delenv("REDIS_DB", raising=False)

    # 2. Define a dependency override for CoreConfig
    def get_test_config():
        # Create a mock CoreConfig, providing mocks for the database and redis
        # configurations that we don't want to instantiate.
        return CoreConfig(
            api_keys=[VALID_API_KEY],
            minio=MinioConfig(
                access_key="minioadmin",
                secret_key=SecretStr("minioadmin"),
                endpoint=f"http://localhost:{os.getenv('S3_PORT')}",
                bucket=os.getenv("S3_BUCKET_NAME"),
            ),
            postgres=create_autospec(PostgresConfig, instance=True),
            redis=create_autospec(RedisConfig, instance=True),
        )

    # 3. Force Celery to run tasks eagerly for synchronous testing
    celery_app.conf.update(
        task_always_eager=True,
        task_store_eager_result=True,
    )

    # 4. Apply dependency overrides
    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_core_config] = get_test_config

    # 5. Clear any registered startup handlers for testing
    app.router.on_startup.clear()

    # 6. Set up mock S3 storage
    with mock_aws():
        # S3 client for the test setup itself
        s3_client = boto3.client("s3", region_name="us-east-1")

        # Override the S3 storage dependency used by the application
        def get_mock_s3_storage():
            config = get_test_config().minio
            # Ensure the bucket exists in the mock environment
            s3_client.create_bucket(Bucket=config.bucket)
            # Inject the mock client
            return S3Storage(config=config, s3_client=s3_client)

        app.dependency_overrides[get_s3_storage] = get_mock_s3_storage

        # Yield the TestClient
        with TestClient(app) as test_client:
            yield test_client

    # 7. Clean up overrides and caches after the test
    app.dependency_overrides.clear()
    get_core_config.cache_clear()

    # Drop tables after the test has finished
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def test_txt_content() -> str:
    return "The sky is blue and the grass is green."


@pytest.fixture
def mock_embedding() -> list[float]:
    # A 1536-dimensional vector of 0.1s, similar to text-embedding-ada-002
    return [0.1] * 1536


# --- E2E API Test ---
@patch("nexusmind.tasks.setup_processor_registry")
@patch("nexusmind.llm.llm_endpoint.litellm.completion")
@patch("nexusmind.llm.llm_endpoint.litellm.embedding")
def test_async_upload_and_chat(
    mock_embedding_call,
    mock_completion_call,
    mock_setup_processor_registry,
    test_txt_content,
    mock_embedding,
    client,  # Use the new client fixture
):
    """
    Tests the full end-to-end flow in a synchronous testing environment.
    1. Upload a file, which is processed immediately due to Celery's eager mode.
    2. Ask a question about the file.
    3. Verify the response.
    """
    # --- Mock S3 and Processor dependencies for the Celery task ---
    # The api_client fixture already handles mocking for the API context.
    # This patch handles mocking for the background Celery task context.
    # s3_storage_mock = client.app.dependency_overrides[get_s3_storage]()

    # Configure the mock processor to use the same mock S3 storage
    processor_mock = MagicMock()
    # Return a real, serializable Chunk object instead of a raw MagicMock
    mock_chunk = Chunk(
        content=test_txt_content,
        page_number=1,
        file_name="test_doc.txt",
        document_id=str(uuid.uuid4()),
    )
    processor_mock.process.return_value = [mock_chunk]

    registry_mock = MagicMock()
    registry_mock.get_processor.return_value = processor_mock

    # Make the patched setup function return our fully mocked registry
    mock_setup_processor_registry.return_value = registry_mock

    # --- Mock LLM services ---
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
    response_upload = client.post(
        "/upload", data={"brain_id": brain_id}, files=files, headers=headers
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


def test_chat_without_api_key(client):
    """Test that a request without an API key is rejected."""
    response = client.post(
        "/chat", json={"brain_id": str(uuid.uuid4()), "question": "test"}
    )
    assert response.status_code == 403
    assert "Not authenticated" in response.text


def test_chat_with_invalid_api_key(client):
    """Test that a request with an invalid API key is rejected."""
    response = client.post(
        "/chat",
        json={"brain_id": str(uuid.uuid4()), "question": "test"},
        headers={"X-API-Key": "invalid-key"},
    )
    assert response.status_code == 403
    assert "Could not validate credentials" in response.text
