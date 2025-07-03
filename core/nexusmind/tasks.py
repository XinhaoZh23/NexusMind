from uuid import UUID

from sqlmodel import Session, select

from core.nexusmind.brain.brain import Brain
from core.nexusmind.celery_app import app
from core.nexusmind.database import engine
from core.nexusmind.files.file import NexusFile
from core.nexusmind.logger import logger
from core.nexusmind.models.files import File, FileStatusEnum
from core.nexusmind.processor.implementations.simple_txt_processor import (
    SimpleTxtProcessor,
)
from core.nexusmind.processor.registry import ProcessorRegistry
from core.nexusmind.storage.s3_storage import S3Storage


def setup_processor_registry() -> ProcessorRegistry:
    """Helper function to initialize and configure the processor registry."""
    storage = S3Storage()  # Use S3 storage now
    registry = ProcessorRegistry()
    registry.register_processor(".txt", SimpleTxtProcessor(storage=storage))
    return registry


@app.task(bind=True)
def process_file(self, file_id: str):
    """
    Celery task to process a file stored in S3.
    It updates the file's status in the database throughout the process.
    """
    logger.info(
        f"Starting file processing task {self.request.id} for file_id: {file_id}"
    )

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

            # 2. Load the associated brain
            try:
                brain = Brain.load(file_record.brain_id)
            except FileNotFoundError:
                logger.warning(
                    f"Brain {file_record.brain_id} not found. Creating a new one."
                )
                brain = Brain(
                    brain_id=file_record.brain_id,
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
            file_record = session.exec(
                select(File).where(File.id == UUID(file_id))
            ).first()
            if file_record:
                file_record.status = FileStatusEnum.FAILURE
                session.add(file_record)
                session.commit()

            self.update_state(state="FAILURE", meta={"error": str(e)})
            raise
