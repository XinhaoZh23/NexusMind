import json
import uuid
from pathlib import Path

from .brain import Brain

BRAIN_STORAGE_PATH = Path("brains")


def get_brain_path(brain_id: uuid.UUID) -> Path:
    """Returns the path to the brain file."""
    BRAIN_STORAGE_PATH.mkdir(exist_ok=True)
    return BRAIN_STORAGE_PATH / f"{brain_id}.json"


def save_brain(brain: Brain):
    """
    Saves the brain's state to a JSON file.
    Also saves the vector store if it exists.
    """
    # Save the main brain configuration
    path = get_brain_path(brain.brain_id)
    with open(path, "w") as f:
        # Pydantic's model_dump_json is perfect for this
        f.write(brain.model_dump_json(indent=4))

    # Save the vector store
    if brain.vector_store:
        brain.vector_store.save_to_disk()


def load_brain(brain_id: uuid.UUID) -> Brain:
    """
    Loads a brain's state from a JSON file.
    """
    path = get_brain_path(brain_id)
    if not path.exists():
        raise FileNotFoundError(f"No brain found with ID {brain_id}")

    with open(path, "r") as f:
        data = json.load(f)
        # Use model_validate to create the instance from data
        # without triggering the custom __init__ method.
        # The initialization of runtime components will be handled
        # by the Brain.load() classmethod.
        return Brain.model_validate(data)
