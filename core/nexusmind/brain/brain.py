import uuid
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, ConfigDict

from core.nexusmind.config import CoreConfig
from core.nexusmind.llm.llm_endpoint import LLMEndpoint


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
    llm_model_name: str
    temperature: float
    max_tokens: int

    # This field will not be part of the serialization
    # as it's a runtime object.
    llm_endpoint: Optional[LLMEndpoint] = Field(None, exclude=True)
    
    def __init__(self, **data):
        super().__init__(**data)
        self.llm_endpoint = self._create_llm_endpoint()

    def _create_llm_endpoint(self) -> LLMEndpoint:
        """Creates the LLM endpoint from the brain's configuration."""
        config = CoreConfig(
            llm_model_name=self.llm_model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return LLMEndpoint(config)
    
    def save(self):
        """Saves the brain's state."""
        from core.nexusmind.brain import serialization
        serialization.save_brain(self)

    @classmethod
    def load(cls, brain_id: uuid.UUID) -> "Brain":
        """Loads a brain's state."""
        from core.nexusmind.brain import serialization
        return serialization.load_brain(brain_id) 