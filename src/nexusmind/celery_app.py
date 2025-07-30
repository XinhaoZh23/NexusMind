from celery import Celery

# Create a Celery instance without any configuration.
# The configuration will be loaded from the main application's settings.
app = Celery("nexusmind_tasks", include=["nexusmind.tasks"])
