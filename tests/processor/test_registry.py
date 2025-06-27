import pytest
from unittest.mock import Mock

from core.nexusmind.processor.processor_base import ProcessorBase
from core.nexusmind.processor.registry import ProcessorRegistry


def test_register_and_get_processor():
    """
    Test registering a processor and retrieving it.
    """
    registry = ProcessorRegistry()
    mock_processor = Mock(spec=ProcessorBase)

    registry.register_processor(".txt", mock_processor)
    retrieved_processor = registry.get_processor("document.txt")
    assert retrieved_processor is mock_processor

    # Test case-insensitivity and with/without dot
    registry.register_processor("PDF", mock_processor)
    retrieved_processor_pdf = registry.get_processor("report.PDF")
    assert retrieved_processor_pdf is mock_processor


def test_get_unregistered_processor():
    """
    Test that getting a processor for an unregistered extension raises an error.
    """
    registry = ProcessorRegistry()
    with pytest.raises(ValueError) as excinfo:
        registry.get_processor("archive.zip")
    assert "No processor registered for file type '.zip'" in str(excinfo.value) 