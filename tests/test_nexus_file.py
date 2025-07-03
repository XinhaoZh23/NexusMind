from uuid import UUID

import pytest

from nexusmind.files.file import NexusFile
from nexusmind.processor.splitter import Chunk


def test_nexus_file_instantiation():
    """
    Test that a NexusFile instance can be created with valid data.
    """
    file_id = UUID(int=1)
    file = NexusFile(
        file_id=file_id,
        file_name="test.txt",
        file_path="/path/to/test.txt",
        metadata={"source": "upload"},
    )
    assert file.file_id == file_id
    assert file.file_name == "test.txt"
    assert file.file_path == "/path/to/test.txt"
    assert file.metadata == {"source": "upload"}


def test_chunk_instantiation():
    """
    Test that a Chunk instance can be created successfully.
    """
    chunk_id = UUID(int=2)
    document_id = UUID(int=3)
    chunk = Chunk(
        chunk_id=chunk_id,
        document_id=document_id,
        content="This is a test chunk.",
        metadata={"page": 1},
    )
    assert chunk.chunk_id == chunk_id
    assert chunk.document_id == document_id
    assert chunk.content == "This is a test chunk."
    assert chunk.metadata == {"page": 1}


def test_metadata_handling():
    """
    Test that metadata dictionaries are correctly handled.
    """
    # Test NexusFile metadata
    file = NexusFile(file_name="test.txt", file_path="/path/to/test.txt")
    assert file.metadata == {}  # Should default to empty dict
    file.metadata["new_key"] = "new_value"
    assert file.metadata["new_key"] == "new_value"

    # Test Chunk metadata
    doc_id = UUID(int=4)
    chunk = Chunk(document_id=doc_id, content="content")
    assert chunk.metadata == {}  # Should default to empty dict
    chunk.metadata["chunk_source"] = "splitter"
    assert chunk.metadata["chunk_source"] == "splitter"
