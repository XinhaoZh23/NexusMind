import uuid
from unittest.mock import Mock

import pytest

from core.nexusmind.brain.brain import Brain
from core.nexusmind.processor.splitter import Chunk
from core.nexusmind.rag.nexus_rag import NexusRAG
from core.nexusmind.storage.vector_store_base import VectorStoreBase


@pytest.fixture
def mock_brain():
    """Fixture to create a mock Brain with a mock LLMEndpoint and VectorStore."""
    brain = Mock(spec=Brain)
    brain.history = []

    # Mock LLM Endpoint
    brain.llm_endpoint = Mock()
    brain.llm_endpoint.get_chat_completion.return_value = "This is the final answer."

    # Mock Vector Store
    brain.vector_store = Mock(spec=VectorStoreBase)
    retrieved_chunks = [Chunk(document_id=uuid.uuid4(), content="The sky is blue.")]
    brain.vector_store.similarity_search.return_value = retrieved_chunks

    return brain


def test_rag_pipeline_uses_vector_store(mock_brain):
    """
    Test the RAG pipeline flow to ensure it uses the VectorStore for retrieval.
    """
    # Arrange
    rag = NexusRAG(brain=mock_brain)
    question = "What color is the sky?"

    # Act
    answer = rag.generate_answer(question)

    # Assert
    # 1. Assert that the vector store's similarity_search was called correctly
    mock_brain.vector_store.similarity_search.assert_called_once_with(query=question)

    # 2. Assert that the prompt sent to the LLM contains the correct context
    call_args = mock_brain.llm_endpoint.get_chat_completion.call_args
    assert call_args is not None
    messages = call_args[0][0]  # First positional argument
    prompt = messages[0]["content"]

    assert "Based on the following context:" in prompt
    assert "The sky is blue." in prompt  # Context from the mocked vector store
    assert "Please answer the question: What color is the sky?" in prompt

    # 3. Assert history update
    assert len(mock_brain.history) == 1
    assert mock_brain.history[0]["user"] == question
    assert mock_brain.history[0]["assistant"] == "This is the final answer."

    # 4. Assert return value
    assert answer == "This is the final answer."
