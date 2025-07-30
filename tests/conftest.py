import json

import pytest


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """
    Creates a consistent, mocked environment for all tests.

    This fixture automatically runs for every test function, ensuring that
    the application's configuration is loaded from a predictable set of
    environment variables, isolating tests from the host system's environment.
    """
    # LLM and Core App Settings
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_api_key")
    monkeypatch.setenv("STORAGE_BASE_PATH", "/tmp/nexusmind_test_storage")

    # Use a JSON-encoded list for API_KEYS
    monkeypatch.setenv("API_KEYS", json.dumps(["test-api-key-from-conftest"]))

    # Celery Configuration
    monkeypatch.setenv("CELERY_BROKER_URL", "redis://localhost:6379/10")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/11")

    # PostgreSQL Configuration (with POSTGRES_ prefix)
    monkeypatch.setenv("POSTGRES_USER", "testuser")
    monkeypatch.setenv("POSTGRES_PASSWORD", "testpassword")
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_PORT", "5433")
    monkeypatch.setenv("POSTGRES_DB", "testdb")

    # Redis Configuration (with REDIS__ prefix for nesting)
    monkeypatch.setenv("REDIS__REDIS_HOST", "localhost")
    monkeypatch.setenv("REDIS__REDIS_PORT", "6380")
    monkeypatch.setenv("REDIS__REDIS_DB", "1")

    # Minio/S3 Configuration (with MINIO_ prefix and aliases)
    monkeypatch.setenv("MINIO_ROOT_USER", "testminiouser")
    monkeypatch.setenv("MINIO_ROOT_PASSWORD", "testminiopassword")
    monkeypatch.setenv("MINIO_ENDPOINT", "localhost:9000")
    monkeypatch.setenv("MINIO_BUCKET", "test-bucket")
