from core.nexusmind.files.file import NexusFile
from core.nexusmind.processor.implementations.simple_txt_processor import SimpleTxtProcessor
from core.nexusmind.storage.local_storage import LocalStorage


def test_simple_txt_processor(tmp_path):
    """
    Test that the SimpleTxtProcessor correctly processes a text file.
    """
    # 1. Setup: Create a temporary storage and a test file
    storage = LocalStorage(base_path=str(tmp_path))
    file_path = "test.txt"
    file_content = "First line.\nSecond line.\n\nThird line."
    storage.save(file_path, file_content.encode("utf-8"))

    # 2. Create a NexusFile object pointing to the test file
    nexus_file = NexusFile(file_name="test.txt", file_path=file_path)

    # 3. Initialize the processor and process the file
    processor = SimpleTxtProcessor(storage=storage)
    chunks = processor.process(nexus_file)

    # 4. Assertions
    assert len(chunks) == 3  # Should skip the empty line
    assert chunks[0].content == "First line."
    assert chunks[1].content == "Second line."
    assert chunks[2].content == "Third line."

    assert chunks[0].document_id == nexus_file.file_id
    assert chunks[1].metadata["line_number"] == 2
    assert chunks[2].metadata["file_name"] == "test.txt" 