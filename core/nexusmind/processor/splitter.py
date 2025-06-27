import uuid
from pydantic import BaseModel, Field


class Chunk(BaseModel):
    """
    Represents a chunk of a document.
    """

    chunk_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    document_id: uuid.UUID
    content: str
    metadata: dict = Field(default_factory=dict) 