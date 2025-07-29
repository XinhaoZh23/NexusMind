from src.nexusmind.config import get_core_config


def test_config_loads_from_test_env():
    """
    Verifies that the configuration is correctly loaded from the 'tests/.env'
    file, which is specified in 'pytest.ini'.
    """
    # Clear cache to ensure we get a fresh instance for this test module
    get_core_config.cache_clear()

    config = get_core_config()

    # Assert that a value from the root of the config is loaded
    assert config.storage_base_path == "/tmp/test_storage"

    # Assert that a value for a nested model is loaded
    assert config.postgres.host == "localhost"
    assert config.redis.host == "localhost"
