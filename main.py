import uuid
from functools import lru_cache
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel, Field

from core.nexusmind.brain.brain import Brain
from core.nexusmind.rag.nexus_rag import NexusRAG
from core.nexusmind.files.file import NexusFile
from core.nexusmind.processor.registry import ProcessorRegistry
from core.nexusmind.processor.implementations.simple_txt_processor import SimpleTxtProcessor
from core.nexusmind.storage.local_storage import LocalStorage
from core.nexusmind.logger import logger
import uvicorn

# --- FastAPI App Initialization ---
app = FastAPI(
    title="NEXUSMIND API",
    description="An API for interacting with the NEXUSMIND RAG system.",
    version="0.1.0",
)

# --- Dependency Injection Setup ---
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
@app.post("/upload")
async def upload_file(
    brain_id: uuid.UUID = Form(...), 
    file: UploadFile = File(...),
    storage: LocalStorage = Depends(get_storage),
    processor_registry: ProcessorRegistry = Depends(get_processor_registry)
):
    """
    Uploads a file, processes it, and adds it to the specified brain's knowledge base.
    """
    brain = get_or_create_brain(brain_id)

    # 1. Save file to local storage
    content = await file.read()
    file_path = storage.save(content, file.filename)
    logger.info(f"File '{file.filename}' uploaded to '{file_path}'.")

    # 2. Create NexusFile instance
    nexus_file = NexusFile(file_name=file.filename, file_path=str(file_path))

    # 3. Process the file to get chunks
    processor = processor_registry.get_processor(nexus_file.file_name)
    if not processor:
        # This part should now be unreachable if the registry is configured correctly
        raise HTTPException(status_code=400, detail=f"No processor found for file type: {nexus_file.extension}")
    
    chunks = processor.process(nexus_file)

    # 4. Add chunks to the brain's vector store
    if brain.vector_store:
        brain.vector_store.add_documents(chunks)
        logger.info(f"Added {len(chunks)} chunks to brain {brain_id}'s vector store.")
    else:
        logger.error(f"Vector store not available for brain {brain_id}.")
        raise HTTPException(status_code=500, detail="Vector store not initialized.")

    return {"message": f"File '{file.filename}' uploaded and processed successfully."}


@app.post("/chat")
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