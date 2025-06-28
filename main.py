import uuid
from functools import lru_cache
from fastapi import (
    FastAPI, UploadFile, File, Form, HTTPException, 
    Depends, BackgroundTasks, Security
)
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from typing import List

from core.nexusmind.brain.brain import Brain
from core.nexusmind.rag.nexus_rag import NexusRAG
from core.nexusmind.files.file import NexusFile
from core.nexusmind.processor.registry import ProcessorRegistry
from core.nexusmind.processor.implementations.simple_txt_processor import SimpleTxtProcessor
from core.nexusmind.storage.local_storage import LocalStorage
from core.nexusmind.logger import logger
from core.nexusmind.config import CoreConfig
import uvicorn

# --- Security and App Initialization ---
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=True)

app = FastAPI(
    title="NEXUSMIND API",
    description="An API for interacting with the NEXUSMIND RAG system.",
    version="0.1.0",
)

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
        raise HTTPException(
            status_code=403, detail="Could not validate credentials"
        )
    return api_key_header

# In-memory storage for task statuses
TASK_STATUSES = {}

@lru_cache
def get_storage() -> LocalStorage:
    """Dependency provider for LocalStorage."""
    return LocalStorage()

@lru_cache
def get_processor_registry() -> ProcessorRegistry:
    """
    Dependency provider for the ProcessorRegistry.
    It creates and configures a singleton instance of the registry.
    """
    logger.info("Creating and configuring processor registry singleton...")
    storage = get_storage()
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

# --- API Endpoints ---
def process_uploaded_file(
    task_id: str,
    brain_id: uuid.UUID,
    file_content: bytes,
    file_name: str,
    storage: LocalStorage,
    processor_registry: ProcessorRegistry,
):
    """
    The background task that processes the file.
    """
    try:
        TASK_STATUSES[task_id] = "PROCESSING"
        
        brain = get_or_create_brain(brain_id)

        # 1. Save file to local storage
        file_path = storage.save(file_content, file_name)
        logger.info(f"File '{file_name}' uploaded to '{file_path}'.")

        # 2. Create NexusFile instance
        nexus_file = NexusFile(file_name=file_name, file_path=str(file_path))

        # 3. Process the file to get chunks
        processor = processor_registry.get_processor(nexus_file.file_name)
        if not processor:
            raise ValueError(f"No processor found for file type: {nexus_file.extension}")
        
        chunks = processor.process(nexus_file)

        # 4. Add chunks to the brain's vector store
        if brain.vector_store:
            brain.vector_store.add_documents(chunks)
            logger.info(f"Added {len(chunks)} chunks to brain {brain_id}'s vector store.")
        else:
            raise ValueError(f"Vector store not available for brain {brain_id}.")

        TASK_STATUSES[task_id] = "SUCCESS"

    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        TASK_STATUSES[task_id] = "FAILURE"

@app.post("/upload", dependencies=[Depends(get_api_key)])
async def upload_file(
    background_tasks: BackgroundTasks,
    brain_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    storage: LocalStorage = Depends(get_storage),
    processor_registry: ProcessorRegistry = Depends(get_processor_registry)
):
    """
    Uploads a file, processes it in the background, and returns a task ID.
    """
    task_id = str(uuid.uuid4())
    TASK_STATUSES[task_id] = "PENDING"
    
    # Read file content in the endpoint
    content = await file.read()

    # Add the processing to background tasks
    background_tasks.add_task(
        process_uploaded_file,
        task_id,
        brain_id,
        content,
        file.filename,
        storage,
        processor_registry
    )

    return JSONResponse(
        status_code=202, 
        content={"task_id": task_id, "message": "File upload accepted and is being processed."}
    )

@app.get("/upload/status/{task_id}")
async def get_upload_status(task_id: str):
    """
    Retrieves the status of a background upload task.
    """
    status = TASK_STATUSES.get(task_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task_id, "status": status}

@app.post("/chat", dependencies=[Depends(get_api_key)])
async def chat_with_brain(request: ChatRequest):
    """
    Handles a chat request by generating an answer from the specified brain.
    """
    try:
        brain = Brain.load(request.brain_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Brain with ID {request.brain_id} not found.")

    # Instantiate RAG with the loaded brain
    rag = NexusRAG(brain=brain)

    # Generate an answer
    answer = rag.generate_answer(request.question)
    
    return {"answer": answer}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 