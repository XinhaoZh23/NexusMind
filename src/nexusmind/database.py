from typing import Optional

from sqlmodel import create_engine
from sqlalchemy.engine import Engine

from .config import get_core_config
from .logger import logger

# Global variable to cache the production engine
_engine: Optional[Engine] = None


def get_engine(db_url: Optional[str] = None, **kwargs) -> Engine:
    """
    Returns a SQLAlchemy engine.

    This function implements a singleton pattern for the production engine.
    If db_url is provided (for testing), it creates a new engine every time.
    If db_url is not provided, it returns a cached engine for production use.

    :param db_url: The database URL to connect to.
    :param kwargs: Additional arguments to pass to create_engine (e.g., poolclass).
    :return: A SQLAlchemy Engine instance.
    """
    global _engine

    if db_url:
        # For tests: create a new engine with the provided URL and kwargs.
        logger.info(f"Creating new test engine for db_url: {db_url}")
        return create_engine(db_url, echo=False, **kwargs)

    # For production: use the cached engine if it exists.
    if _engine is None:
        logger.info("Creating new production database engine...")
        try:
            config = get_core_config()
            production_db_url = config.postgres.get_db_url()
            _engine = create_engine(production_db_url, echo=False)
            logger.info("Production database engine created and cached.")
        except Exception as e:
            logger.error("Failed to create database engine: {}", e, exc_info=True)
            raise
    return _engine


def get_session():
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
