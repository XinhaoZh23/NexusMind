import pytest
from unittest.mock import patch, Mock
from core.nexusmind.config import CoreConfig
from core.nexusmind.llm.llm_endpoint import LLMEndpoint


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

    llm_endpoint = LLMEndpoint(config=core_config)
    messages = [{"role": "user", "content": "Hello"}]

    # Act
    result = llm_endpoint.get_chat_completion(messages)

    # Assert
    mock_completion.assert_called_once_with(
        model="test-model",
        messages=messages,
        temperature=0.5,
        max_tokens=100
    )
    assert result == "This is a test response."


@patch("litellm.embedding")
def test_get_embedding(mock_embedding, core_config):
    """
    Test the get_embedding method with a mocked litellm.embedding call.
    """
    # Arrange
    data_item_mock = Mock()
    data_item_mock.embedding = [0.1, 0.2, 0.3]
    mock_response = Mock()
    mock_response.data = [data_item_mock]
    mock_embedding.return_value = mock_response

    llm_endpoint = LLMEndpoint(config=core_config)
    text_to_embed = "This is a test text."

    # Act
    result = llm_endpoint.get_embedding(text_to_embed)

    # Assert
    mock_embedding.assert_called_once_with(
        model="text-embedding-ada-002",
        input=[text_to_embed]
    )
    assert result == [0.1, 0.2, 0.3]


@patch("litellm.completion", side_effect=Exception("API Error"))
def test_get_chat_completion_error_handling(mock_completion, core_config):
    """
    Test that get_chat_completion handles exceptions gracefully.
    """
    # Arrange
    llm_endpoint = LLMEndpoint(config=core_config)
    messages = [{"role": "user", "content": "Hello"}]

    # Act
    result = llm_endpoint.get_chat_completion(messages)

    # Assert
    assert result == "" 