"""
LLM integration module for SudokuAI.
"""

from .client import LLMClient, create_client
from .player import LLMPlayer, play_game
from .evaluator import LLMEvaluator, evaluate_model
from .recorder import GameRecorder
from .prompts import build_step_prompt, build_oneshot_prompt, parse_move, parse_solution

__all__ = [
    "LLMClient",
    "create_client",
    "LLMPlayer",
    "play_game",
    "LLMEvaluator",
    "evaluate_model",
    "GameRecorder",
    "build_step_prompt",
    "build_oneshot_prompt",
    "parse_move",
    "parse_solution",
]