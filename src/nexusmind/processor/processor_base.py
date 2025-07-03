from abc import ABC, abstractmethod
from typing import List

from ..files.file import NexusFile
from .splitter import Chunk


class ProcessorBase(ABC):
    """
    Abstract base class for document processors.
    """

    @abstractmethod
    def process(self, file: NexusFile) -> List[Chunk]:
        """
        Process a file and return a list of chunks.
        """
        pass
