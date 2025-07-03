from unittest.mock import MagicMock, patch

import pytest

from nexusmind.brain.brain import Brain
from nexusmind.brain.serialization import BRAIN_STORAGE_PATH, load_brain, save_brain
from nexusmind.llm.llm_endpoint import LLMEndpoint


@pytest.fixture
def mock_llm_endpoint():
    pass


def test_brain_initialization():
    """
    Test that a Brain instance is initialized correctly.
    """
    brain = Brain(llm_model_name="test-gpt", temperature=0.5, max_tokens=50)
    assert brain.name == "Default Brain"
    assert brain.history == []
    assert brain.llm_endpoint is not None
    assert brain.llm_endpoint.model_name == "test-gpt"
    assert brain.llm_endpoint.temperature == 0.5
    assert brain.llm_endpoint.max_tokens == 50


def test_brain_history_update():
    """
    Test that the conversation history can be updated.
    """
    brain = Brain(llm_model_name="test-gpt", temperature=0.5, max_tokens=50)
    new_entry = {"user": "Hello", "assistant": "Hi there!"}
    brain.history.append(new_entry)
    assert len(brain.history) == 1
    assert brain.history[0] == new_entry


def test_save_and_load_brain(tmp_path):
    """
    Test saving a brain's state and then loading it back.
    """
    # Override the default storage path to use the temporary directory
    original_path = BRAIN_STORAGE_PATH
    try:
        # Ugly but effective for testing: modify the global path
        from nexusmind.brain import serialization

        serialization.BRAIN_STORAGE_PATH = tmp_path

        # 1. Create and modify a brain instance
        brain_to_save = Brain(
            llm_model_name="test-gpt-save", temperature=0.8, max_tokens=150
        )
        brain_to_save.history.append({"user": "Question 1", "assistant": "Answer 1"})
        brain_to_save.name = "Saved Brain"
        brain_id = brain_to_save.brain_id

        # 2. Save the brain
        brain_to_save.save()

        # 3. Load the brain
        loaded_brain = Brain.load(brain_id)

        # 4. Assert that the loaded brain has the same state
        assert loaded_brain.brain_id == brain_id
        assert loaded_brain.name == "Saved Brain"
        assert loaded_brain.history[0]["user"] == "Question 1"
        assert loaded_brain.llm_model_name == "test-gpt-save"
        assert loaded_brain.temperature == 0.8
        assert loaded_brain.llm_endpoint is not None  # Ensure it's re-created
        assert loaded_brain.llm_endpoint.max_tokens == 150

    finally:
        # Restore the original path to avoid side effects
        from nexusmind.brain import serialization

        serialization.BRAIN_STORAGE_PATH = original_path
