from typing import List

from core.nexusmind.files.file import NexusFile
from core.nexusmind.processor.processor_base import ProcessorBase
from core.nexusmind.processor.splitter import Chunk
from core.nexusmind.storage.storage_base import StorageBase


class SimpleTxtProcessor(ProcessorBase):
    """
    A simple processor for .txt files.
    It splits the document by lines.
    """

    def __init__(self, storage: StorageBase):
        self.storage = storage

    def process(self, file: NexusFile) -> List[Chunk]:
        """
        Processes a .txt file by reading its content from storage
        and splitting it into chunks line by line.
        """
        content_bytes = self.storage.get(file.file_path)
        content_str = content_bytes.decode("utf-8")
        lines = content_str.splitlines()

        chunks = []
        for i, line in enumerate(lines):
            if line.strip():  # Avoid creating empty chunks
                chunk = Chunk(
                    document_id=file.file_id,
                    content=line,
                    metadata={
                        "file_name": file.file_name,
                        "line_number": i + 1,
                    },
                )
                chunks.append(chunk)

        return chunks 