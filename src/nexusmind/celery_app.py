from celery import Celery

from .config import CoreConfig

# Load application configuration
config = CoreConfig()

# Initialize Celery
app = Celery(
    "nexusmind_tasks",
    broker=config.redis_url,
    backend=config.redis_url,
    include=["core.nexusmind.tasks"],  # Points to the future tasks file
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
