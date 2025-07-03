from typing import List

import litellm


class LLMEndpoint:
    """
    A unified endpoint for interacting with various Large Language Models (LLMs)
    using the litellm library.
    """

    def __init__(self, model_name: str, temperature: float, max_tokens: int):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        # litellm can automatically handle API keys from environment variables,
        # so we don't necessarily need to pass them explicitly.

    def get_chat_completion(self, messages: list, optional_params: dict = None) -> str:
        """
        Get a text response from the configured chat model.

        :param messages: A list of messages in OpenAI format.
        :param optional_params: A dictionary of optional parameters for
            litellm.completion.
        :return: The string content of the model's response.
        """
        params = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if optional_params:
            params.update(optional_params)

        try:
            response = litellm.completion(**params)
            return response.choices[0].message.content or ""
        except Exception as e:
            # Handle potential API errors gracefully
            print(f"An error occurred while calling the LLM: {e}")
            # Depending on the desired behavior, you might want to re-raise,
            # return a default value, or log the error.
            return ""

    def get_embedding(self, text: str) -> List[float]:
        """
        Get the vector embedding for a given text.

        :param text: The input text to embed.
        :return: A list of floats representing the embedding.
        """
        try:
            response = litellm.embedding(model="text-embedding-ada-002", input=[text])
            return response["data"][0]["embedding"]
        except Exception as e:
            print(f"An error occurred while getting embeddings: {e}")
            return []
