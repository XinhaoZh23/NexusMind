import uuid
import pytest
from unittest.mock import Mock, patch

from core.nexusmind.brain.brain import Brain
from core.nexusmind.rag.nexus_rag import NexusRAG
from core.nexusmind.processor.splitter import Chunk


@pytest.fixture
def mock_brain():
    """Fixture to create a mock Brain with a mock LLMEndpoint."""
    brain = Mock(spec=Brain)
    brain.history = []
    brain.llm_endpoint = Mock()
    brain.llm_endpoint.get_chat_completion.return_value = "This is the final answer."
    return brain

@pytest.fixture
def sample_knowledge_base():
    """Fixture for a sample knowledge base of Chunks."""
    doc_id = uuid.uuid4()
    return [
        Chunk(document_id=doc_id, content="The sky is blue."),
        Chunk(document_id=doc_id, content="Gold is a yellow metal."),
        Chunk(document_id=doc_id, content="The sun is a star and it is very hot.")
    ]


def test_rag_pipeline(mock_brain, sample_knowledge_base):
    """
    Test the full RAG pipeline flow.
    """
    # Arrange
    rag = NexusRAG(brain=mock_brain, knowledge_base=sample_knowledge_base)
    question = "What color is the sky?"

    # Act
    answer = rag.generate_answer(question)

    # Assert
    # 1. Assert prompt format
    # Check that get_chat_completion was called and capture its arguments
    call_args = mock_brain.llm_endpoint.get_chat_completion.call_args
    assert call_args is not None
    messages = call_args[0][0]  # First positional argument
    prompt = messages[0]['content']

    assert "Based on the following context:" in prompt
    assert "The sky is blue." in prompt  # Retrieved context
    assert "Please answer the question: What color is the sky?" in prompt

    # 2. Assert history update
    assert len(mock_brain.history) == 1
    assert mock_brain.history[0]["user"] == question
    assert mock_brain.history[0]["assistant"] == "This is the final answer."

    # 3. Assert return value
    assert answer == "This is the final answer."

def test_retrieval_logic(sample_knowledge_base):
    """
    Test the pseudo-retrieval logic more directly.
    """
    # Arrange
    mock_brain_instance = Mock(spec=Brain)
    rag = NexusRAG(brain=mock_brain_instance, knowledge_base=sample_knowledge_base)
    
    # Act
    retrieved = rag._retrieve("tell me about gold metal")
    
    # Assert
    assert len(retrieved) == 1
    assert retrieved[0].content == "Gold is a yellow metal." 