"""
Unified LLM client supporting multiple providers.
"""

from typing import Optional, List
from ..core import LLMConfig
from .providers.ollama import OllamaProvider
from .providers.openai_compatible import (
    OpenAICompatibleProvider, OpenAIProvider, AliyunProvider,
    MinimaxProvider, DeepSeekProvider, MoonshotProvider, ZhipuProvider
)
from .providers.base import BaseProvider, LLMResponse


class LLMClient:
    """Unified client for different LLM providers."""

    PROVIDER_MAP = {
        "ollama": OllamaProvider,
        "openai": OpenAIProvider,
        "aliyun": AliyunProvider,
        "minimax": MinimaxProvider,
        "deepseek": DeepSeekProvider,
        "moonshot": MoonshotProvider,
        "zhipu": ZhipuProvider,
    }

    def __init__(self, config: LLMConfig):
        self.config = config
        self.provider = self._create_provider(config)

    def _create_provider(self, config: LLMConfig) -> BaseProvider:
        provider_class = self.PROVIDER_MAP.get(config.provider, OpenAICompatibleProvider)
        
        if config.provider == "ollama":
            return provider_class(
                api_base=config.api_base,
                model=config.model,
                api_key=config.api_key,
            )
        else:
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

    def list_models(self) -> List[str]:
        if hasattr(self.provider, 'list_models'):
            return self.provider.list_models()
        return []

    @property
    def model_name(self) -> str:
        return self.config.model


def create_client(config: LLMConfig) -> LLMClient:
    return LLMClient(config)


def test_api_key(provider: str, api_key: str, api_base: str = None, model: str = None) -> dict:
    """Test if an API key is valid for a provider."""
    from ..core import DEFAULT_PROVIDERS
    
    default_config = DEFAULT_PROVIDERS.get(provider)
    if not default_config:
        return {"valid": False, "error": f"Unknown provider: {provider}"}
    
    config = LLMConfig(
        name=provider,
        provider=provider,
        api_base=api_base or default_config.api_base,
        model=model or default_config.model,
        api_key=api_key,
    )
    
    try:
        client = LLMClient(config)
        is_valid = client.test_connection()
        if is_valid:
            return {"valid": True, "models": client.list_models()}
        else:
            return {"valid": False, "error": "Connection test failed"}
    except Exception as e:
        return {"valid": False, "error": str(e)}