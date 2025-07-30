from typing import Optional, Generator
from functools import lru_cache
from threading import Lock

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.exc import ValidationError

from .config import get_core_config
from .logger import logger

# Global variable to cache the production engine
_engine: Optional[Engine] = None
_lock = Lock()


@lru_cache()
def get_engine(db_url: str | None = None, connect_args: dict | None = None) -> Engine:
    """
    Returns a SQLAlchemy Engine instance.

    Uses a cached engine instance for the same database URL to avoid
    creating multiple engines for the same database.

    Args:
        db_url: The database URL to connect to.
        connect_args: A dictionary of arguments to pass to the engine.

    Returns:
        A SQLAlchemy Engine instance.
    """
    print(f"--- [DEBUG] get_engine CALLED ---")
    print(f"--- [DEBUG] Received db_url: {db_url} ---")

    global _engine
    if db_url:
        # If a specific db_url is provided (typically for tests), create a new engine
        return create_engine(db_url, connect_args=connect_args or {})

    # Production path: use cached singleton engine
    if _engine is None:
        with _lock:
            if _engine is None:
                try:
                    config = get_core_config()
                    prod_db_url = config.postgres.get_db_url()
                    print(f"--- [DEBUG] Production DB URL: {prod_db_url} ---")
                    _engine = create_engine(prod_db_url, echo=True)
                except ValidationError as e:
                    logger.error(
                        "Failed to create database engine due to config validation error: {}",
                        e,
                        exc_info=True,
                    )
                    raise
    return _engine


def get_session() -> Generator[Session, None, None]:
    """
    Dependency provider for FastAPI to get a database session.
    It ensures that the session is always closed after the request is finished.
    """
    engine = get_engine()
    with Session(engine) as session:
        try:
            yield session
        finally:
            session.close()


def create_db_and_tables():
    """
    Utility function to create all tables defined by SQLModel metadata.
    This is useful for initializing the database for the first time.
    """
    logger.info("Creating database tables...")
    engine = get_engine()
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
