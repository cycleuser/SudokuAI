"""
OpenAI-compatible provider for various LLM services.
Supports OpenAI, Aliyun (DashScope), Minimax, DeepSeek, etc.
"""

from typing import Optional
import requests
from .base import BaseProvider, LLMResponse


class OpenAICompatibleProvider(BaseProvider):
    """Provider for OpenAI-compatible APIs."""

    def __init__(self, api_base: str, model: str, api_key: str = "", provider_type: str = "openai"):
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.provider_type = provider_type

    def _get_headers(self) -> dict:
        headers = {
            "Content-Type": "application/json",
        }
        
        if self.provider_type == "minimax":
            headers["Authorization"] = f"Bearer {self.api_key}"
        else:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers

    def chat(self, messages: list[dict], temperature: float = 0.0, 
             max_tokens: int = 2048) -> LLMResponse:
        url = f"{self.api_base}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        response = requests.post(
            url, 
            json=payload, 
            headers=self._get_headers(),
            timeout=120
        )
        
        if response.status_code != 200:
            error_msg = response.text
            raise Exception(f"API error {response.status_code}: {error_msg}")
        
        data = response.json()

        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            model=data.get("model", self.model),
            usage=data.get("usage", {}),
            finish_reason=data["choices"][0].get("finish_reason", "stop"),
        )

    def test_connection(self) -> bool:
        if not self.api_key:
            return False
        
        try:
            url = f"{self.api_base}/chat/completions"
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 5,
            }
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False

    def list_models(self) -> list[str]:
        if not self.api_key:
            return []
        
        try:
            url = f"{self.api_base}/models"
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])
                return [m.get("id", m.get("name", "")) for m in models]
            return []
        except Exception:
            return []


class AliyunProvider(OpenAICompatibleProvider):
    """Provider for Aliyun DashScope API."""
    
    DEFAULT_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    DEFAULT_MODEL = "qwen-turbo"
    KNOWN_MODELS = [
        "qwen-turbo",
        "qwen-plus",
        "qwen-max",
        "qwen-max-longcontext",
        "qwen2.5-72b-instruct",
        "qwen2.5-32b-instruct",
        "qwen2.5-14b-instruct",
        "qwen2.5-7b-instruct",
    ]

    def __init__(self, api_base: str = None, model: str = None, api_key: str = ""):
        super().__init__(
            api_base=api_base or self.DEFAULT_BASE,
            model=model or self.DEFAULT_MODEL,
            api_key=api_key,
            provider_type="aliyun"
        )
    
    def list_models(self) -> list[str]:
        return self.KNOWN_MODELS


class MinimaxProvider(OpenAICompatibleProvider):
    """Provider for Minimax API."""
    
    DEFAULT_BASE = "https://api.minimax.chat/v1"
    DEFAULT_MODEL = "abab6.5-chat"
    KNOWN_MODELS = [
        "abab6.5-chat",
        "abab6.5s-chat",
        "abab5.5-chat",
        "abab5.5s-chat",
    ]

    def __init__(self, api_base: str = None, model: str = None, api_key: str = ""):
        super().__init__(
            api_base=api_base or self.DEFAULT_BASE,
            model=model or self.DEFAULT_MODEL,
            api_key=api_key,
            provider_type="minimax"
        )
    
    def list_models(self) -> list[str]:
        return self.KNOWN_MODELS


class DeepSeekProvider(OpenAICompatibleProvider):
    """Provider for DeepSeek API."""
    
    DEFAULT_BASE = "https://api.deepseek.com/v1"
    DEFAULT_MODEL = "deepseek-chat"
    KNOWN_MODELS = [
        "deepseek-chat",
        "deepseek-coder",
        "deepseek-reasoner",
    ]

    def __init__(self, api_base: str = None, model: str = None, api_key: str = ""):
        super().__init__(
            api_base=api_base or self.DEFAULT_BASE,
            model=model or self.DEFAULT_MODEL,
            api_key=api_key,
            provider_type="deepseek"
        )
    
    def list_models(self) -> list[str]:
        return self.KNOWN_MODELS


class OpenAIProvider(OpenAICompatibleProvider):
    """Provider for OpenAI API."""
    
    DEFAULT_BASE = "https://api.openai.com/v1"
    DEFAULT_MODEL = "gpt-4o-mini"
    KNOWN_MODELS = [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4",
        "gpt-3.5-turbo",
        "o1-preview",
        "o1-mini",
    ]

    def __init__(self, api_base: str = None, model: str = None, api_key: str = ""):
        super().__init__(
            api_base=api_base or self.DEFAULT_BASE,
            model=model or self.DEFAULT_MODEL,
            api_key=api_key,
            provider_type="openai"
        )
    
    def list_models(self) -> list[str]:
        return self.KNOWN_MODELS


class MoonshotProvider(OpenAICompatibleProvider):
    """Provider for Moonshot (Kimi) API."""
    
    DEFAULT_BASE = "https://api.moonshot.cn/v1"
    DEFAULT_MODEL = "moonshot-v1-8k"
    KNOWN_MODELS = [
        "moonshot-v1-8k",
        "moonshot-v1-32k",
        "moonshot-v1-128k",
    ]

    def __init__(self, api_base: str = None, model: str = None, api_key: str = ""):
        super().__init__(
            api_base=api_base or self.DEFAULT_BASE,
            model=model or self.DEFAULT_MODEL,
            api_key=api_key,
            provider_type="moonshot"
        )
    
    def list_models(self) -> list[str]:
        return self.KNOWN_MODELS


class ZhipuProvider(OpenAICompatibleProvider):
    """Provider for Zhipu AI API."""
    
    DEFAULT_BASE = "https://open.bigmodel.cn/api/paas/v4"
    DEFAULT_MODEL = "glm-4-flash"
    KNOWN_MODELS = [
        "glm-4",
        "glm-4-flash",
        "glm-4-plus",
        "glm-4-air",
        "glm-4-airx",
    ]

    def __init__(self, api_base: str = None, model: str = None, api_key: str = ""):
        super().__init__(
            api_base=api_base or self.DEFAULT_BASE,
            model=model or self.DEFAULT_MODEL,
            api_key=api_key,
            provider_type="zhipu"
        )
    
    def list_models(self) -> list[str]:
        return self.KNOWN_MODELS