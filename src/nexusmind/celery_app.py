from celery import Celery

from nexusmind.config import get_core_config

# Use the centralized config function to get a config instance
config = get_core_config()

# Initialize Celery directly with values from the config instance.
# This ensures a single source of truth for configuration.
app = Celery(
    "nexusmind_tasks",
    broker=config.celery_broker_url,
    backend=config.celery_result_backend,
    include=["nexusmind.tasks"],
)

# Optional: Update Celery configuration with more settings if needed
app.conf.update(
    task_track_started=True,
)

# The following is no longer needed and has been removed:
# - A custom CeleryConfig class, which was an unnecessary wrapper.
# - Manual construction of redis_url, as we now use the values from CoreConfig.
# - The redundant and problematic app.config_from_object() call.

if __name__ == "__main__":
    app.start()
