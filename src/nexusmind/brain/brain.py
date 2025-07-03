import uuid
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ..llm.llm_endpoint import LLMEndpoint
from ..logger import get_logger
from ..storage.faiss_vector_store import FaissVectorStore
from ..storage.vector_store_base import VectorStoreBase

logger = get_logger(__name__)


class Brain(BaseModel):
    """
    The Brain class is the central control unit.
    It manages the state and orchestrates the other components.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    brain_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str = "Default Brain"
    history: List[Dict[str, str]] = Field(default_factory=list)

    # Configuration fields
    llm_model_name: str = Field(...)
    temperature: float = Field(...)
    max_tokens: int = Field(...)

    # This field will not be part of the serialization
    # as it's a runtime object.
    llm_endpoint: Optional[LLMEndpoint] = Field(None, exclude=True)
    vector_store: Optional[VectorStoreBase] = Field(None, exclude=True)

    def __init__(self, **data):
        super().__init__(**data)
        self.llm_endpoint = self._create_llm_endpoint()
        self.vector_store = self._create_vector_store()

    def _create_llm_endpoint(self) -> LLMEndpoint:
        """Creates the LLM endpoint from the brain's configuration."""
        return LLMEndpoint(
            model_name=self.llm_model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

    def _create_vector_store(self) -> VectorStoreBase:
        """Creates the vector store."""
        # For now, we are hardcoding FaissVectorStore.
        # This could be made configurable in the future.
        store_path = f"storage/vs_{self.brain_id}.index"
        return FaissVectorStore(llm_endpoint=self.llm_endpoint, store_path=store_path)

    def save(self):
        """Saves the brain's state."""
        logger.info(f"Saving brain state for brain_id: {self.brain_id}")
        from . import serialization

        serialization.save_brain(self)

    @classmethod
    def load(cls, brain_id: uuid.UUID) -> "Brain":
        """Loads a brain's state."""
        logger.info(f"Loading brain state for brain_id: {brain_id}")
        from . import serialization

        return serialization.load_brain(brain_id)
