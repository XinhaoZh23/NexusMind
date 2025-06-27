from core.quivr_core.base_config import BaseConfig


class CoreConfig(BaseConfig):
    llm_model_name: str = "gpt-4"
    temperature: float = 0.0
    max_tokens: int = 1000 