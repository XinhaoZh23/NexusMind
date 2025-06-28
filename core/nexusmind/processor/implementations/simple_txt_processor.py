from typing import List

from core.nexusmind.files.file import NexusFile
from core.nexusmind.processor.processor_base import ProcessorBase
from core.nexusmind.processor.splitter import Chunk
from core.nexusmind.storage.storage_base import StorageBase
from core.nexusmind.logger import logger


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
        logger.info(f"Processing file: {file.file_name} (Path: {file.file_path})")
        
        try:
            content_bytes = self.storage.get(file.file_path)
            content_str = content_bytes.decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to read or decode file {file.file_name}: {e}")
            return []
            
        lines = content_str.splitlines()
        logger.debug(f"File content split into {len(lines)} lines. Lines: {lines}")

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

        logger.info(f"Created {len(chunks)} chunks from file {file.file_name}.")
        return chunks 