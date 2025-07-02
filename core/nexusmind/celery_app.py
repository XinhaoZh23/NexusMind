from celery import Celery
from core.nexusmind.config import CoreConfig

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

if __name__ == "__main__":
    app.start() 