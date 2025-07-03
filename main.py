import uuid
from functools import lru_cache
from typing import Dict

import uvicorn
from celery.result import AsyncResult
from fastapi import Depends, FastAPI, File, Form, HTTPException, Security, UploadFile
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from sqlalchemy.orm import Session

from nexusmind.brain.brain import Brain
from nexusmind.celery_app import app as celery_app
from nexusmind.config import CoreConfig, get_core_config
from nexusmind.database import create_db_and_tables, engine, get_session
from nexusmind.logger import get_logger
from nexusmind.models.files import File as FileModel
from nexusmind.models.files import FileStatusEnum
from nexusmind.processor.implementations.simple_txt_processor import (
    SimpleTxtProcessor,
)
from nexusmind.processor.registry import ProcessorRegistry
from nexusmind.rag.nexus_rag import NexusRAG
from nexusmind.storage.s3_storage import S3Storage, get_s3_storage
from nexusmind.tasks import process_file

# --- Security and App Initialization ---
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=True)

app = FastAPI(
    title="NEXUSMIND API",
    description="An API for interacting with the NEXUSMIND RAG system.",
    version="0.1.0",
)


@app.on_event("startup")
def on_startup():
    # Create database tables if they don't exist
    create_db_and_tables()
    # Ensure the S3 bucket exists
    s3_storage = get_s3_storage()
    s3_storage.create_bucket_if_not_exists()


# --- Configuration and Dependency Injection ---
@lru_cache
def get_core_config() -> CoreConfig:
    return CoreConfig()


async def get_api_key(
    api_key_header: str = Security(API_KEY_HEADER),
    config: CoreConfig = Depends(get_core_config),
):
    """Dependency to verify the API key."""
    if not config.api_keys:
        logger.warning("API keys are not configured. Endpoint is unprotected.")
        return api_key_header
    if api_key_header not in config.api_keys:
        raise HTTPException(status_code=403, detail="Could not validate credentials")
    return api_key_header


# In-memory storage for task statuses
TASK_STATUSES = {}


@lru_cache
def get_s3_storage() -> S3Storage:
    """Dependency provider for S3Storage."""
    return S3Storage()


@lru_cache
def get_processor_registry(
    storage: S3Storage = Depends(get_s3_storage),
) -> ProcessorRegistry:
    """
    Dependency provider for the ProcessorRegistry.
    It creates and configures a singleton instance of the registry.
    """
    logger.info("Creating and configuring processor registry singleton...")
    registry = ProcessorRegistry()
    simple_txt_processor = SimpleTxtProcessor(storage=storage)
    registry.register_processor(".txt", simple_txt_processor)
    logger.info("Processor registry configured.")
    return registry


# --- Helper Functions ---
def get_or_create_brain(brain_id: uuid.UUID) -> Brain:
    """
    Loads a brain if it exists, otherwise creates a new one with default settings.
    """
    try:
        # Load the brain if it exists
        brain = Brain.load(brain_id)
        logger.info(f"Loaded existing brain with ID: {brain_id}")
        return brain
    except FileNotFoundError:
        # Create a new brain with default settings if not found
        logger.info(f"No brain found for ID: {brain_id}. Creating a new one.")
        brain = Brain(
            brain_id=brain_id,
            name=f"Brain {brain_id}",
            llm_model_name="gpt-4o",  # Default model
            temperature=0.0,
            max_tokens=256,
        )
        brain.save()
        logger.info(f"Saved new brain with ID: {brain_id}")
        return brain


# --- API Request Models ---
class ChatRequest(BaseModel):
    question: str
    brain_id: uuid.UUID


class UploadResponse(BaseModel):
    task_id: str
    message: str


class StatusResponse(BaseModel):
    task_id: str
    status: str
    result: Dict | str | None


# --- API Endpoints ---
@app.post("/upload", dependencies=[Depends(get_api_key)], response_model=UploadResponse)
async def upload_file(
    brain_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    storage: S3Storage = Depends(get_s3_storage),
    session: Session = Depends(get_session),
):
    """
    Uploads a file to S3, creates a database record, and queues it for processing.
    """
    try:
        # 1. Save file to S3
        content = await file.read()
        s3_path = storage.save(content, file.filename)
        logger.info(f"File '{file.filename}' uploaded to S3 at '{s3_path}'.")

        # 2. Create a record in the database
        db_file = FileModel(
            file_name=file.filename,
            s3_path=s3_path,
            brain_id=brain_id,
            status=FileStatusEnum.PENDING,
        )
        session.add(db_file)
        session.commit()
        session.refresh(db_file)
        logger.info(f"Created file record in DB with ID: {db_file.id}")

        # 3. Queue the processing task
        task = process_file.delay(str(db_file.id))

        return UploadResponse(
            task_id=task.id, message="File upload accepted and is being processed."
        )
    except Exception as e:
        logger.error(
            f"Failed to queue file processing for {file.filename}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to start file processing.")


@app.get("/upload/status/{task_id}", response_model=StatusResponse)
async def get_upload_status(task_id: str, session: Session = Depends(get_session)):
    """
    Retrieves the status of a file processing task from Celery.
    This endpoint can also be expanded to include the database status.
    """
    task_result = AsyncResult(task_id, app=celery_app)

    status = task_result.status
    result = task_result.result

    if task_result.failed():
        result = str(task_result.result)

    # Optional: You could also query your `FileModel` here using the task_id
    # if you were to store it, to provide even more detailed status.

    return StatusResponse(
        task_id=task_id,
        status=status,
        result=result,
    )


@app.post("/chat", dependencies=[Depends(get_api_key)])
async def chat_with_brain(request: ChatRequest):
    """
    Handles a chat request by generating an answer from the specified brain.
    """
    try:
        brain = Brain.load(request.brain_id)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Brain with ID {request.brain_id} not found."
        )

    # Instantiate RAG with the loaded brain
    rag = NexusRAG(brain=brain)

    # Generate an answer
    answer = rag.generate_answer(request.question)

    return {"answer": answer}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
