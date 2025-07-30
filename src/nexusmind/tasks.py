from uuid import UUID

import boto3
from sqlmodel import Session, select

from .brain.brain import Brain
from .celery_app import app
from .config import get_core_config
from .database import get_engine
from .files.file import NexusFile
from .logger import logger
from .models.files import File, FileStatusEnum
from .processor.implementations.simple_txt_processor import SimpleTxtProcessor
from .processor.registry import ProcessorRegistry
from .storage.s3_storage import S3Storage


def setup_processor_registry() -> ProcessorRegistry:
    """Helper function to initialize and configure the processor registry."""
    # Since this runs in a separate Celery process, we need to initialize
    # the config and S3 client here, similar to how it's done in main.py
    config = get_core_config()
    client_kwargs = {
        "aws_access_key_id": config.minio.access_key,
        "aws_secret_access_key": config.minio.secret_key.get_secret_value(),
        "region_name": "us-east-1",  # Added for consistency
    }
    if config.minio.endpoint:
        client_kwargs["endpoint_url"] = config.minio.endpoint

    s3_client = boto3.client("s3", **client_kwargs)
    storage = S3Storage(config=config.minio, s3_client=s3_client)

    registry = ProcessorRegistry()
    registry.register_processor(".txt", SimpleTxtProcessor(storage=storage))
    return registry


@app.task(bind=True)
def process_file(self, file_id: str, brain_id: str):
    """
    Celery task to process a file stored in S3.
    It updates the file's status in the database throughout the process.
    """
    logger.info(
        f"Starting file processing task {self.request.id} "
        f"for file_id: {file_id} and brain_id: {brain_id}"
    )

    engine = get_engine()  # Call the factory to get the engine
    with Session(engine) as session:
        try:
            # 1. Fetch the file record from the database
            file_record = session.exec(
                select(File).where(File.id == UUID(file_id))
            ).first()
            if not file_record:
                raise ValueError(
                    f"File record with id {file_id} not found in the database."
                )

            # Update status to PROCESSING
            file_record.status = FileStatusEnum.PROCESSING
            session.add(file_record)
            session.commit()

            # 2. Load the associated brain using the provided brain_id
            target_brain_id = UUID(brain_id)
            try:
                brain = Brain.load(target_brain_id)
            except FileNotFoundError:
                logger.warning(
                    f"Brain {target_brain_id} not found. Creating a new one."
                )
                brain = Brain(
                    brain_id=target_brain_id,
                    name=f"Brain {target_brain_id}",
                    llm_model_name="gpt-4o-mini",
                    temperature=0.0,
                    max_tokens=100,
                )

            # 3. Create NexusFile and get processor
            # The file_path is now the S3 key
            nexus_file = NexusFile(
                file_name=file_record.file_name, file_path=file_record.s3_path
            )
            registry = setup_processor_registry()
            processor = registry.get_processor(file_record.file_name)
            if not processor:
                raise ValueError(
                    f"No processor found for file type: {file_record.file_name}"
                )

            # 4. Process the file into chunks
            chunks = processor.process(nexus_file)

            # 5. Add chunks to the brain's vector store
            if chunks:
                brain.vector_store.add_documents(chunks)
                brain.save()  # Save brain state after modification
                logger.info(
                    f"Successfully added {len(chunks)} chunks from "
                    f"{file_record.file_name} to brain {brain.brain_id}."
                )
            else:
                logger.warning(
                    f"No chunks were created from file {file_record.file_name}."
                )

            # 6. Update status to SUCCESS
            # We need to refresh the file_record to avoid detached instance error
            session.refresh(file_record)
            file_record.status = FileStatusEnum.SUCCESS
            session.add(file_record)
            session.commit()

            return {
                "status": "SUCCESS",
                "message": f"File {file_record.file_name} processed successfully.",
            }

        except Exception as e:
            logger.error(
                f"Error processing file_id {file_id} in task {self.request.id}: {e}",
                exc_info=True,
            )
            # Rollback any changes and update status to FAILURE
            session.rollback()
            file_record_to_fail = session.exec(
                select(File).where(File.id == UUID(file_id))
            ).first()
            if file_record_to_fail:
                file_record_to_fail.status = FileStatusEnum.FAILURE
                session.add(file_record_to_fail)
                session.commit()

            self.update_state(state="FAILURE", meta={"error": str(e)})
            raise
