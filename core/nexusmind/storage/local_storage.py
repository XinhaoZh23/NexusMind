import os
import uuid
from pathlib import Path
from typing import Optional

from core.nexusmind.storage.storage_base import StorageBase


class LocalStorage(StorageBase):
    """
    Local storage implementation.
    Saves files to the local filesystem.
    """

    def __init__(self, base_path: str = "storage"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_full_path(self, filename: str) -> Path:
        """Helper to get the full path safely."""
        return self.base_path / filename

    def save(self, file_content: bytes, file_path: Optional[str] = None) -> str:
        """Saves content to a file."""
        if file_path is None:
            file_path = str(uuid.uuid4())

        full_path = self._get_full_path(file_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, "wb") as f:
            f.write(file_content)

        return file_path

    def get(self, file_path: str) -> bytes:
        """
        Get content from a local file.
        """
        full_path = self._get_full_path(file_path)
        with open(full_path, "rb") as f:
            return f.read()

    def delete(self, file_path: str) -> None:
        """
        Delete a local file.
        """
        full_path = self._get_full_path(file_path)
        if full_path.exists():
            os.remove(full_path)

    def exists(self, file_path: str) -> bool:
        """
        Check if a local file exists.
        """
        full_path = self._get_full_path(file_path)
        return full_path.exists()
