import logging
import os
import sys

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
    enqueue=True,  # Make logging asynchronous, non-blocking
    backtrace=True,  # Show the full stack trace on exceptions
    diagnose=True,  # Add exception details for debugging
)

# Export the configured logger for use in other modules
__all__ = ["logger"]


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name: The name of the logger.

    Returns:
        The logger instance.
    """
    return logging.getLogger(name)


# Configure loguru to intercept standard logging
class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


# Setup standard logging to be intercepted by loguru
logging.basicConfig(handlers=[InterceptHandler()], level=0)
