from sqlmodel import Session, create_engine

from core.nexusmind.config import CoreConfig
from core.nexusmind.logger import logger

# Load configuration
config = CoreConfig()

# Create the database engine
# The 'echo=True' argument is useful for debugging as it logs all SQL statements.
# It should probably be turned off in production.
try:
    engine = create_engine(config.database_url, echo=True)
    logger.info("Database engine created successfully.")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    # Exit or handle gracefully if the database connection is critical at startup
    raise


def get_session():
    """
    Dependency provider for FastAPI to get a database session.
    It ensures that the session is always closed after the request is finished.
    """
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
    # This import is placed here to ensure all models are loaded
    # before we try to create the tables.
    from sqlmodel import SQLModel

    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
