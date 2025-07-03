from unittest.mock import Mock, patch

import pytest
from litellm.caching import Cache

from nexusmind.config import CoreConfig
from nexusmind.llm.llm_endpoint import LLMEndpoint


@pytest.fixture
def core_config():
    """Pytest fixture for a CoreConfig instance."""
    return CoreConfig(llm_model_name="test-model", temperature=0.5, max_tokens=100)


@patch("litellm.completion")
def test_get_chat_completion(mock_completion, core_config):
    """
    Test the get_chat_completion method with a mocked litellm.completion call.
    """
    # Arrange
    message_mock = Mock()
    message_mock.content = "This is a test response."
    choice_mock = Mock()
    choice_mock.message = message_mock
    mock_response = Mock()
    mock_response.choices = [choice_mock]
    mock_completion.return_value = mock_response

    llm_endpoint = LLMEndpoint(
        model_name=core_config.llm_model_name,
        temperature=core_config.temperature,
        max_tokens=core_config.max_tokens,
    )

    # Act
    response = llm_endpoint.get_chat_completion(
        messages=[{"role": "user", "content": "Hello"}]
    )

    # Assert
    mock_completion.assert_called_once_with(
        model="test-model",
        messages=[{"role": "user", "content": "Hello"}],
        temperature=0.5,
        max_tokens=100,
    )
    assert response == "This is a test response."


@patch("litellm.embedding")
def test_get_embedding(mock_embedding, core_config):
    """
    Test the get_embedding method with a mocked litellm.embedding call.
    """
    # Arrange
    # The response from litellm.embedding is dict-like, so we mock it as a dict.
    mock_response = {"data": [{"embedding": [0.1, 0.2, 0.3]}]}
    mock_embedding.return_value = mock_response

    llm_endpoint = LLMEndpoint(
        model_name=core_config.llm_model_name,
        temperature=core_config.temperature,
        max_tokens=core_config.max_tokens,
    )

    # Act
    embedding = llm_endpoint.get_embedding("test text")

    # Assert
    mock_embedding.assert_called_once_with(
        model="text-embedding-ada-002", input=["test text"]
    )
    assert embedding == [0.1, 0.2, 0.3]


@patch("litellm.completion", side_effect=Exception("API Error"))
def test_get_chat_completion_error_handling(mock_completion, core_config):
    """
    Test that get_chat_completion handles exceptions gracefully.
    """
    # Arrange
    llm_endpoint = LLMEndpoint(
        model_name=core_config.llm_model_name,
        temperature=core_config.temperature,
        max_tokens=core_config.max_tokens,
    )

    # Act
    response = llm_endpoint.get_chat_completion(
        messages=[{"role": "user", "content": "Hello"}]
    )

    # Assert
    assert response == ""


def test_llm_endpoint_initialization():
    """Tests the initialization of the LLMEndpoint."""
