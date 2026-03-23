"""
Unified LLM client supporting multiple providers.
"""

from typing import Optional
from ..core import LLMConfig
from .providers.ollama import OllamaProvider
from .providers.base import BaseProvider, LLMResponse


class LLMClient:
    """Unified client for different LLM providers."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.provider = self._create_provider(config)

    def _create_provider(self, config: LLMConfig) -> BaseProvider:
        provider_map = {
            "ollama": OllamaProvider,
        }

        provider_class = provider_map.get(config.provider, OllamaProvider)
        return provider_class(
            api_base=config.api_base,
            model=config.model,
            api_key=config.api_key,
        )

    def chat(self, user: str, system: Optional[str] = None, 
             temperature: Optional[float] = None, 
             max_tokens: Optional[int] = None) -> LLMResponse:
        messages = self.provider.format_messages(system, user)
        temp = temperature if temperature is not None else self.config.temperature
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        return self.provider.chat(messages, temperature=temp, max_tokens=tokens)

    def test_connection(self) -> bool:
        return self.provider.test_connection()

    @property
    def model_name(self) -> str:
        return self.config.model


def create_client(config: LLMConfig) -> LLMClient:
    return LLMClient(config)