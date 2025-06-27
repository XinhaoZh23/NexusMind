import uuid
from pydantic import BaseModel, Field


class NexusFile(BaseModel):
    """
    Represents a file in the system.
    """

    file_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    file_name: str
    file_path: str
    metadata: dict = Field(default_factory=dict) 