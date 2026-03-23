"""
Base provider interface for LLM backends.
"""

from abc import ABC, abstractmethod
from typing import Optional, Iterator
from dataclasses import dataclass


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: dict
    finish_reason: str = "stop"


class BaseProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, api_base: str, model: str, api_key: str = ""):
        self.api_base = api_base
        self.model = model
        self.api_key = api_key

    @abstractmethod
    def chat(self, messages: list[dict], temperature: float = 0.0, 
             max_tokens: int = 2048) -> LLMResponse:
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        pass

    def format_messages(self, system: Optional[str], user: str) -> list[dict]:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})
        return messages