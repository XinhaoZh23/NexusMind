from celery import Celery
from celery.schedules import crontab

from nexusmind.config import get_core_config

# Use the centralized config function
config = get_core_config()


class CeleryConfig:
    # Construct Redis URL from the structured config
    redis_url = (
        f"redis://{config.redis.host}:{config.redis.port}/"
        f"{config.redis.db}"
    )

    # Initialize Celery
    app = Celery(
        "nexusmind_tasks",
        broker=redis_url,
        backend=redis_url,
        include=["nexusmind.tasks"],
    )

    # Optional: Update Celery configuration with more settings if needed
    app.conf.update(
        task_track_started=True,
    )

    # Load celery config from Pydantic settings
    # The namespace='CELERY' argument means all celery-related settings
    # should be in uppercase and prefixed with `CELERY_` in your config file
    # (e.g., CELERY_BROKER_URL, CELERY_RESULT_BACKEND).
    app.config_from_object(CoreConfig(), namespace="CELERY")

if __name__ == "__main__":
    app.start()
