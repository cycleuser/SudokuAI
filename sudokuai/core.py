"""
Core data structures and types for SudokuAI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime
from enum import Enum
import json


class Difficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"
    MASTER = "master"


class PlayMode(Enum):
    STEP_BY_STEP = "step"
    ONE_SHOT = "oneshot"


@dataclass
class ToolResult:
    """Standard result type for all API functions."""

    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


@dataclass
class SudokuGame:
    """Represents a Sudoku game instance."""

    id: str
    puzzle: list[list[int]]
    solution: list[list[int]]
    difficulty: str
    clues: int
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "puzzle": self.puzzle,
            "solution": self.solution,
            "difficulty": self.difficulty,
            "clues": self.clues,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SudokuGame":
        return cls(
            id=data["id"],
            puzzle=data["puzzle"],
            solution=data["solution"],
            difficulty=data["difficulty"],
            clues=data["clues"],
            created_at=datetime.fromisoformat(
                data.get("created_at", datetime.now().isoformat())
            ),
        )


@dataclass
class GameMove:
    """Represents a single move in a Sudoku game."""

    game_id: str
    step: int
    row: int
    col: int
    value: int
    is_valid: bool
    reasoning: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "game_id": self.game_id,
            "step": self.step,
            "row": self.row,
            "col": self.col,
            "value": self.value,
            "is_valid": self.is_valid,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class LLMConfig:
    """Configuration for an LLM provider."""

    name: str
    provider: str
    api_base: str
    model: str
    api_key: str = "ollama"
    temperature: float = 0.0
    max_tokens: int = 2048

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "provider": self.provider,
            "api_base": self.api_base,
            "model": self.model,
            "api_key": self.api_key,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LLMConfig":
        return cls(
            name=data["name"],
            provider=data["provider"],
            api_base=data["api_base"],
            model=data["model"],
            api_key=data.get("api_key", "ollama"),
            temperature=data.get("temperature", 0.0),
            max_tokens=data.get("max_tokens", 2048),
        )


@dataclass
class PlayResult:
    """Result of an LLM playing a Sudoku game."""

    game_id: str
    model_name: str
    mode: str
    completed: bool
    correct: bool
    total_moves: int
    valid_moves: int
    invalid_moves: int
    time_elapsed: float
    difficulty: str
    moves: list[GameMove] = field(default_factory=list)
    final_board: list[list[int]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "game_id": self.game_id,
            "model_name": self.model_name,
            "mode": self.mode,
            "completed": self.completed,
            "correct": self.correct,
            "total_moves": self.total_moves,
            "valid_moves": self.valid_moves,
            "invalid_moves": self.invalid_moves,
            "time_elapsed": self.time_elapsed,
            "difficulty": self.difficulty,
            "moves": [m.to_dict() for m in self.moves],
            "final_board": self.final_board,
        }


@dataclass
class EvaluationResult:
    """Result of evaluating an LLM on multiple Sudoku games."""

    model_name: str
    provider: str
    total_games: int
    completed_games: int
    correct_games: int
    overall_accuracy: float
    total_time: float
    results_by_difficulty: dict[str, dict] = field(default_factory=dict)
    play_results: list[PlayResult] = field(default_factory=list)
    evaluated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "model_name": self.model_name,
            "provider": self.provider,
            "total_games": self.total_games,
            "completed_games": self.completed_games,
            "correct_games": self.correct_games,
            "overall_accuracy": self.overall_accuracy,
            "total_time": self.total_time,
            "results_by_difficulty": self.results_by_difficulty,
            "play_results": [r.to_dict() for r in self.play_results],
            "evaluated_at": self.evaluated_at.isoformat(),
        }


DEFAULT_PROVIDERS = {
    "ollama": LLMConfig(
        name="ollama",
        provider="ollama",
        api_base="http://localhost:11434/v1",
        model="gemma3:4b",
        api_key="ollama",
    ),
    "openai": LLMConfig(
        name="openai",
        provider="openai",
        api_base="https://api.openai.com/v1",
        model="gpt-4o-mini",
        api_key="",
    ),
    "custom": LLMConfig(
        name="custom",
        provider="custom",
        api_base="",
        model="",
        api_key="",
    ),
}
