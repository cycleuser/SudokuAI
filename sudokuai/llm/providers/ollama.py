"""
Ollama provider for local LLM inference.
"""

from typing import Optional
import requests
from .base import BaseProvider, LLMResponse


class OllamaProvider(BaseProvider):
    """Provider for Ollama local inference."""

    DEFAULT_BASE = "http://localhost:11434/v1"
    DEFAULT_MODEL = "gemma3:4b"

    def __init__(
        self, api_base: str = None, model: str = None, api_key: str = "ollama"
    ):
        self.api_base = api_base or self.DEFAULT_BASE
        self.model = model or self.DEFAULT_MODEL
        self.api_key = api_key

    def chat(
        self, messages: list[dict], temperature: float = 0.0, max_tokens: int = 2048
    ) -> LLMResponse:
        url = f"{self.api_base}/chat/completions"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()

        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            model=data.get("model", self.model),
            usage=data.get("usage", {}),
            finish_reason=data["choices"][0].get("finish_reason", "stop"),
        )

    def test_connection(self) -> bool:
        try:
            url = f"{self.api_base.replace('/v1', '')}/api/tags"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m["name"] for m in models]
                return self.model in model_names or any(
                    self.model in n for n in model_names
                )
            return False
        except Exception:
            return False

    def list_models(self) -> list[str]:
        try:
            url = f"{self.api_base.replace('/v1', '')}/api/tags"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return [m["name"] for m in response.json().get("models", [])]
            return []
        except Exception:
            return []
