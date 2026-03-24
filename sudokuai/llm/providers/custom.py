"""
Custom LLM provider - user-defined API configuration.
Supports any OpenAI-compatible API (OpenAI, Claude, Aliyun, MiniMax, etc.)
"""

from typing import Optional, List
import requests
from .base import BaseProvider, LLMResponse


class CustomProvider(BaseProvider):
    """Provider for any OpenAI-compatible API."""

    def __init__(self, api_base: str, model: str, api_key: str = ""):
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.api_key = api_key

    def _get_headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

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
            error_msg = response.text[:200]
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
                timeout=15
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
                return [m.get("id", m.get("name", "")) for m in models if m.get("id") or m.get("name")]
            return []
        except Exception:
            return []


def validate_api_key(api_base: str, api_key: str, model: str = None) -> dict:
    """Validate an API key for any OpenAI-compatible API."""
    if not api_key:
        return {"valid": False, "error": "API key is required"}
    
    if not api_base:
        return {"valid": False, "error": "API base URL is required"}
    
    provider = CustomProvider(
        api_base=api_base,
        model=model or "gpt-3.5-turbo",
        api_key=api_key,
    )
    
    try:
        is_valid = provider.test_connection()
        if is_valid:
            models = provider.list_models()
            return {"valid": True, "models": models}
        return {"valid": False, "error": "Connection test failed"}
    except Exception as e:
        return {"valid": False, "error": str(e)[:100]}