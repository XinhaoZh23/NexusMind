import sys
import os
from loguru import logger

# Default log level to INFO if not set in environment
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()

# Remove the default logger configuration
logger.remove()

# Configure a new logger to output JSON to stderr
# This is ideal for containerized environments and log collectors
logger.add(
    sys.stderr,
    level=log_level,
    serialize=True,  # This is the key for structured, JSON logging
    enqueue=True,    # Make logging asynchronous, non-blocking
    backtrace=True,  # Show the full stack trace on exceptions
    diagnose=True,   # Add exception details for debugging
)

# Export the configured logger for use in other modules
__all__ = ["logger"] 