from functools import lru_cache

from sqlmodel import Session, SQLModel, create_engine

from .config import get_core_config
from .logger import logger


@lru_cache()
def get_engine():
    """
    Creates and returns a new SQLAlchemy engine instance.
    The `lru_cache` decorator ensures that the engine is created only once.
    """
    logger.info("Creating new database engine...")
    config = get_core_config()
    try:
        engine = create_engine(config.postgres.get_db_url(), echo=True)
        logger.info("Database engine created successfully.")
        return engine
    except Exception as e:
        logger.error(f"Failed to create database engine: {e}")
        raise


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
