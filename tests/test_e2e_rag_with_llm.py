import os
import pytest
from pathlib import Path
from dotenv import load_dotenv

from core.nexusmind.brain.brain import Brain
from core.nexusmind.rag.nexus_rag import NexusRAG
from core.nexusmind.files.file import NexusFile
from core.nexusmind.storage.local_storage import LocalStorage
from core.nexusmind.storage.faiss_vector_store import FaissVectorStore
from core.nexusmind.processor.implementations.simple_txt_processor import (
    SimpleTxtProcessor,
)

# Load environment variables from .env file
load_dotenv()


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not found in .env"
)
def test_end_to_end_rag_with_gpt4o_mini(tmp_path: Path):
    """
    An end-to-end test that uses a real LLM (gpt-4o-mini) to answer
    a question based on a file.
    """
    # 1. Setup: Create a dummy file in a temporary directory
    test_file_name = "test.txt"
    test_file_path = tmp_path / test_file_name
    test_file_content = "The meaning of life is 42."
    test_file_path.write_text(test_file_content)

    # 2. Components Initialization
    storage = LocalStorage(base_path=str(tmp_path))
    nexus_file = NexusFile(file_name=test_file_name, file_path=test_file_name)

    # 3. Create a Brain instance
    brain = Brain(llm_model_name="gpt-4o-mini", temperature=0.0, max_tokens=100)
    
    # Override the default vector store to use the temp path
    vector_store_path = str(tmp_path / "test_vector_store.index")
    brain.vector_store = FaissVectorStore(
        llm_endpoint=brain.llm_endpoint, store_path=vector_store_path
    )

    # 4. Process the file and add it to the vector store
    processor = SimpleTxtProcessor(storage=storage)
    chunks = processor.process(file=nexus_file)
    brain.vector_store.add_documents(chunks)

    # 5. Execute RAG pipeline
    rag = NexusRAG(brain=brain)
    question = "What is the 42?"
    answer = rag.generate_answer(question)

    # Print the full response from the LLM
    print(f"LLM Full Response: {answer}")

    # 6. Assert the answer
    assert "42" in answer, f"LLM did not return the correct answer. Got: {answer}" 