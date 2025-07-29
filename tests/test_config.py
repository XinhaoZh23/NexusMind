import pytest
from src.nexusmind.config import get_core_config


# def test_loads_dev_env_by_default():
#     """
#     Verifies that when no environment is specified, the configuration is
#     loaded from the default 'tests/.env' file.
#     """
#     # Explicitly call with app_env=None to simulate default behavior
#     config = get_core_config(app_env=None)
#     
#     # Assert that the value comes from 'tests/.env'
#     assert config.postgres.host == "localhost-dev"


def test_loads_prod_env_when_app_env_is_production():
    """
    Verifies that when 'production' is specified, the configuration is
    loaded from the 'tests/.env.prod' file.
    """
    # Explicitly call with app_env="production"
    config = get_core_config(app_env="production")
    
    # Assert that the value comes from 'tests/.env.prod'
    assert config.postgres.host == "remote-prod-db"
