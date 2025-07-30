import os
import uuid
from unittest.mock import ANY, MagicMock, patch, create_autospec

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws
from pydantic import SecretStr
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from main import app, get_core_config
from nexusmind.base_config import MinioConfig, PostgresConfig, RedisConfig
from nexusmind.celery_app import app as celery_app
from nexusmind.config import CoreConfig
from nexusmind.database import get_engine, get_session
from nexusmind.processor.splitter import Chunk
from nexusmind.storage.s3_storage import S3Storage, get_s3_storage
from nexusmind.models.files import File as FileModel

VALID_API_KEY = "test-key"

# This engine will be used for all tests, created by our flexible get_engine function.
engine = get_engine(
    db_url="sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
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
        # Using session.get_bind() to get the engine associated with the session
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
@patch("main.process_file.delay")
def test_upload_and_verify_task_dispatch(
    mock_process_file_delay,
    test_txt_content,
    client,
):
    """
    Tests the /upload endpoint as a pure unit test.
    - Verifies that the endpoint returns 200 OK.
    - Verifies that the file metadata is correctly saved to the database.
    - Verifies that the Celery task (`process_file.delay`) is called once.
    """
    headers = {"X-API-Key": VALID_API_KEY}
    brain_id = str(uuid.uuid4())
    files = {"file": ("test_doc.txt", test_txt_content.encode("utf-8"), "text/plain")}

    # --- 1. Upload the file ---
    response_upload = client.post(
        "/upload", data={"brain_id": brain_id}, files=files, headers=headers
    )

    # --- 2. Assertions ---
    # Assert that the API call was successful
    assert response_upload.status_code == 200

    # Assert that the Celery task was called, indicating successful dispatch
    mock_process_file_delay.assert_called_once()

    # Optional but recommended: Verify the task was called with the correct file_id
    # To do this, we need a session to query the database
    with Session(engine) as session:
        file_record = session.query(FileModel).one_or_none()
        assert file_record is not None
        assert file_record.file_name == "test_doc.txt"

        # Check that the first argument of the call matches the created file_id
        call_args = mock_process_file_delay.call_args[0]
        assert call_args[0] == str(file_record.id)
        assert call_args[1] == brain_id


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
