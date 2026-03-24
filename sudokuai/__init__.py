"""
SudokuAI - A Sudoku game platform for LLM evaluation.

This package provides:
- Sudoku game generation with multiple difficulty levels
- LLM integration for autonomous gameplay
- Evaluation and benchmarking tools for LLM reasoning capabilities
- Multiple interfaces: CLI, GUI (PySide6), and Web (Flask)
"""

__version__ = "1.0.3"
__author__ = "SudokuAI Team"

from .api import (
    generate_sudoku,
    solve_sudoku,
    validate_sudoku,
    llm_play_sudoku,
    evaluate_llm,
    generate_report,
    list_llm_providers,
    list_available_models,
    add_llm_provider,
    ToolResult,
)
from .core import SudokuGame, LLMConfig, EvaluationResult, PlayMode

__all__ = [
    "__version__",
    "__author__",
    "generate_sudoku",
    "solve_sudoku",
    "validate_sudoku",
    "llm_play_sudoku",
    "evaluate_llm",
    "generate_report",
    "list_llm_providers",
    "list_available_models",
    "add_llm_provider",
    "ToolResult",
    "SudokuGame",
    "LLMConfig",
    "EvaluationResult",
    "PlayMode",
]
