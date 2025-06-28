from core.nexusmind.base_config import BaseConfig


class CoreConfig(BaseConfig):
    llm_model_name: str = "gpt-4o"
    temperature: float = 0.0
    max_tokens: int = 1000
    api_keys: list[str] = [] 