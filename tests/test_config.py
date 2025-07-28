import os
import pytest
from src.nexusmind.config import get_core_config, _core_config_cache


@pytest.fixture(autouse=True)
def manage_test_environment():
    """
    A fixture that runs before and after each test in this module.
    1. It changes the current working directory to the 'tests' folder
       so that the config loader can find the test-specific .env files.
    2. It clears our custom config cache to ensure test isolation.
    3. It changes the directory back to the original after the test.
    """
    original_cwd = os.getcwd()
    tests_dir = os.path.join(original_cwd, "tests")
    
    # Skip these tests if the 'tests' directory doesn't exist
    if not os.path.isdir(tests_dir):
        pytest.skip("Could not find 'tests' directory. Skipping config loading tests.")
        
    os.chdir(tests_dir)
    _core_config_cache.clear()
    
    yield
    
    # Clean up after the test
    _core_config_cache.clear()
    os.chdir(original_cwd)


def test_loads_dev_env_by_default(monkeypatch):
    """
    Verifies that when APP_ENV is not set, the configuration is loaded
    from the default '.env' file within the 'tests' directory.
    """
    # Ensure the APP_ENV variable is not set for this test
    monkeypatch.delenv("APP_ENV", raising=False)
    
    config = get_core_config()
    
    # Assert that the value comes from 'tests/.env'
    assert config.postgres.host == "localhost-dev"


def test_loads_prod_env_when_app_env_is_production(monkeypatch):
    """
    Verifies that when APP_ENV is set to 'production', the configuration
    is loaded from the '.env.prod' file within the 'tests' directory.
    """
    # Set the APP_ENV to 'production' for this test
    monkeypatch.setenv("APP_ENV", "production")
    
    config = get_core_config()
    
    # Assert that the value comes from 'tests/.env.prod'
    assert config.postgres.host == "remote-prod-db"
