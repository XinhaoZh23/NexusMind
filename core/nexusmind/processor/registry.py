import os
from typing import Dict
from core.nexusmind.processor.processor_base import ProcessorBase


class ProcessorRegistry:
    """
    A registry for document processors.
    It maps file extensions to processor instances.
    """

    def __init__(self):
        self._processors: Dict[str, ProcessorBase] = {}

    def register_processor(self, file_extension: str, processor: ProcessorBase):
        """
        Register a processor for a given file extension.
        """
        normalized_ext = file_extension.lower()
        if not normalized_ext.startswith("."):
            normalized_ext = "." + normalized_ext
        self._processors[normalized_ext] = processor

    def get_processor(self, file_path: str) -> ProcessorBase:
        """
        Get the appropriate processor for a given file path based on its extension.
        """
        _, file_extension = os.path.splitext(file_path)
        normalized_ext = file_extension.lower()

        processor = self._processors.get(normalized_ext)
        if processor is None:
            raise ValueError(f"No processor registered for file type '{normalized_ext}'")
        return processor 