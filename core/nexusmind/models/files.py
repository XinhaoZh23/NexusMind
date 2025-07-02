import uuid
import enum
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class FileStatusEnum(enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class File(SQLModel, table=True):
    # The unique identifier for the file record in the database.
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)

    # The name of the uploaded file.
    file_name: str = Field(index=True)

    # The path or key of the file in the S3 bucket.
    s3_path: str

    # The processing status of the file.
    status: FileStatusEnum = Field(default=FileStatusEnum.PENDING)

    # The ID of the brain this file is associated with.
    brain_id: uuid.UUID = Field(index=True)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        # Pydantic-specific configuration
        arbitrary_types_allowed = True 