import os
import tempfile
import uuid
from unittest.mock import MagicMock, Mock

import numpy as np
import pytest

from nexusmind.llm.llm_endpoint import LLMEndpoint
from nexusmind.processor.splitter import Chunk
from nexusmind.storage.faiss_vector_store import FaissVectorStore

# Predefined vectors for testing
VECTOR_CAT = np.array([0.1, 0.1, 0.8]).astype("float32")
VECTOR_DOG = np.array([0.8, 0.1, 0.1]).astype("float32")
VECTOR_TECH = np.array([0.1, 0.8, 0.1]).astype("float32")


@pytest.fixture
def mock_llm_endpoint():
    """Fixture for a mock LLMEndpoint with predefined embeddings."""
    endpoint = Mock(spec=LLMEndpoint)

    def get_embedding_side_effect(text: str):
        if "cat" in text:
            return VECTOR_CAT.tolist()
        if "dog" in text:
            return VECTOR_DOG.tolist()
        if "tech" in text:
            return VECTOR_TECH.tolist()
        return np.random.rand(3).astype("float32").tolist()

    endpoint.get_embedding.side_effect = get_embedding_side_effect
    return endpoint


@pytest.fixture
def sample_chunks():
    """Fixture for a list of sample chunks."""
    doc_id = uuid.uuid4()
    return [
        Chunk(document_id=doc_id, content="All about cats."),
        Chunk(document_id=doc_id, content="All about dogs."),
        Chunk(document_id=doc_id, content="All about technology."),
    ]


def test_add_and_search(mock_llm_endpoint, sample_chunks):
    """
    Test adding documents to the vector store and performing a similarity search.
    """
    # Arrange
    vector_store = FaissVectorStore(llm_endpoint=mock_llm_endpoint)

    # Act: Add documents
    vector_store.add_documents(sample_chunks)

    # Assert that index was created
    assert vector_store.index is not None
    assert vector_store.index.ntotal == 3

    # Act: Search for "cat"
    search_results_cat = vector_store.similarity_search(
        query="a query about a cat", k=1
    )

    # Assert: The most similar chunk should be the one about cats
    assert len(search_results_cat) == 1
    assert search_results_cat[0].content == "All about cats."

    # Act: Search for "dog"
    search_results_dog = vector_store.similarity_search(
        query="a query about a dog", k=1
    )

    # Assert: The most similar chunk should be the one about dogs
    assert len(search_results_dog) == 1
    assert search_results_dog[0].content == "All about dogs."


def test_empty_search(mock_llm_endpoint):
    """
    Test that searching an empty vector store returns an empty list.
    """
    vector_store = FaissVectorStore(llm_endpoint=mock_llm_endpoint)
    results = vector_store.similarity_search(query="anything")
    assert results == []


def create_mock_embedding_and_chunk(embedding_dim=128):
    """Helper function to create a mock embedding and chunk."""
