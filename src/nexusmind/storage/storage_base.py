from abc import ABC, abstractmethod


class StorageBase(ABC):
    """
    Abstract base class for storage.
    All storage implementations must inherit from this class.
    """

    @abstractmethod
    def save(self, file_path: str, content: bytes) -> None:
        """
        Save content to a specified path.
        """
        pass

    @abstractmethod
    def get(self, file_path: str) -> bytes:
        """
        Get content from a specified path.
        """
        pass

    @abstractmethod
    def delete(self, file_path: str) -> None:
        """
        Delete a file from a specified path.
        """
        pass

    @abstractmethod
    def exists(self, file_path: str) -> bool:
        """
        Check if a file exists at a specified path.
        """
        pass
