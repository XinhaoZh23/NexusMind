from abc import ABC, abstractmethod
from typing import List

from core.nexusmind.processor.splitter import Chunk


class VectorStoreBase(ABC):
    """
    Abstract base class for vector stores.
    """

    @abstractmethod
    def add_documents(self, chunks: List[Chunk]) -> None:
        """
        Add documents to the vector store.
        This involves generating embeddings and indexing them.
        """
        pass

    @abstractmethod
    def similarity_search(self, query: str, k: int = 5) -> List[Chunk]:
        """
        Perform a similarity search against the vector store.
        """
        pass
