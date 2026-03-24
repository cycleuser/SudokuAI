"""
Unified LLM client supporting multiple providers.
"""

from typing import Optional, List
from ..core import LLMConfig
from .providers.ollama import OllamaProvider
from .providers.custom import CustomProvider
from .providers.base import BaseProvider, LLMResponse


class LLMClient:
    """Unified client for different LLM providers."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.provider = self._create_provider(config)

    def _create_provider(self, config: LLMConfig) -> BaseProvider:
        if config.provider == "ollama":
            return OllamaProvider(
                api_base=config.api_base,
                model=config.model,
                api_key=config.api_key or "ollama",
            )
        else:
            return CustomProvider(
                api_base=config.api_base,
                model=config.model,
                api_key=config.api_key,
            )

    def chat(
        self,
        user: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        messages = self.provider.format_messages(system, user)
        temp = temperature if temperature is not None else self.config.temperature
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        return self.provider.chat(messages, temperature=temp, max_tokens=tokens)

    def test_connection(self) -> bool:
        return self.provider.test_connection()

    def list_models(self) -> List[str]:
        if hasattr(self.provider, "list_models"):
            return self.provider.list_models()
        return []

    @property
    def model_name(self) -> str:
        return self.config.model


def create_client(config: LLMConfig) -> LLMClient:
    return LLMClient(config)


def test_api_key(api_base: str, api_key: str, model: str = None) -> dict:
    """Test if an API key is valid for an OpenAI-compatible API."""
    from .providers.custom import validate_api_key

    return validate_api_key(api_base, api_key, model)
