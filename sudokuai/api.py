"""
Unified API for SudokuAI with OpenAI function-calling tools pattern.
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from .core import (
    ToolResult,
    SudokuGame,
    LLMConfig,
    EvaluationResult,
    PlayResult,
    PlayMode,
    DEFAULT_PROVIDERS,
)
from .sudoku.generator import SudokuGenerator
from .sudoku.solver import solve_puzzle, is_solvable
from .sudoku.validator import is_valid_solution
from .llm.player import play_game
from .llm.evaluator import evaluate_model
from .report.generator import generate_evaluation_report, generate_comparison_report

_providers: Dict[str, LLMConfig] = dict(DEFAULT_PROVIDERS)


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "generate_sudoku",
            "description": "Generate a Sudoku puzzle with specified difficulty level",
            "parameters": {
                "type": "object",
                "properties": {
                    "difficulty": {
                        "type": "string",
                        "enum": ["easy", "medium", "hard", "expert", "master"],
                        "description": "Difficulty level for the puzzle",
                    }
                },
                "required": ["difficulty"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "solve_sudoku",
            "description": "Solve a Sudoku puzzle and return the solution",
            "parameters": {
                "type": "object",
                "properties": {
                    "puzzle": {
                        "type": "array",
                        "items": {"type": "array", "items": {"type": "integer"}},
                        "description": "9x9 grid representing the puzzle (0 for empty cells)",
                    }
                },
                "required": ["puzzle"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "validate_sudoku",
            "description": "Validate if a Sudoku solution is correct",
            "parameters": {
                "type": "object",
                "properties": {
                    "solution": {
                        "type": "array",
                        "items": {"type": "array", "items": {"type": "integer"}},
                        "description": "9x9 grid representing the solution to validate",
                    }
                },
                "required": ["solution"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "llm_play_sudoku",
            "description": "Have an LLM play a Sudoku game and record the process",
            "parameters": {
                "type": "object",
                "properties": {
                    "difficulty": {
                        "type": "string",
                        "enum": ["easy", "medium", "hard"],
                        "description": "Difficulty level",
                    },
                    "provider": {
                        "type": "string",
                        "description": "LLM provider name (e.g., 'ollama')",
                    },
                    "model": {
                        "type": "string",
                        "description": "Model name to use",
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["step", "oneshot"],
                        "description": "Play mode: step-by-step or one-shot",
                    },
                },
                "required": ["difficulty", "provider"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "evaluate_llm",
            "description": "Evaluate an LLM's Sudoku solving ability across multiple games",
            "parameters": {
                "type": "object",
                "properties": {
                    "provider": {"type": "string", "description": "LLM provider name"},
                    "model": {"type": "string", "description": "Model name"},
                    "games_per_difficulty": {
                        "type": "integer",
                        "description": "Number of games per difficulty level",
                    },
                    "difficulties": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Difficulty levels to test",
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["step", "oneshot"],
                        "description": "Play mode",
                    },
                },
                "required": ["provider"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_report",
            "description": "Generate a Markdown evaluation report",
            "parameters": {
                "type": "object",
                "properties": {
                    "evaluation_json": {
                        "type": "string",
                        "description": "JSON string of EvaluationResult",
                    },
                },
                "required": ["evaluation_json"],
            },
        },
    },
]


def generate_sudoku(difficulty: str = "medium") -> ToolResult:
    try:
        game_data = SudokuGenerator.generate_game(difficulty)
        game = SudokuGame(
            id=f"game_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            puzzle=game_data["puzzle"],
            solution=game_data["solution"],
            difficulty=difficulty,
            clues=game_data["clues"],
        )
        return ToolResult(
            success=True,
            data=game.to_dict(),
            metadata={"difficulty": difficulty, "clues": game.clues},
        )
    except Exception as e:
        return ToolResult(success=False, error=str(e))


def solve_sudoku(puzzle: List[List[int]]) -> ToolResult:
    try:
        solution = solve_puzzle(puzzle)
        if solution:
            return ToolResult(
                success=True,
                data=solution,
                metadata={
                    "original_clues": sum(
                        1 for row in puzzle for cell in row if cell != 0
                    )
                },
            )
        return ToolResult(success=False, error="Puzzle is not solvable")
    except Exception as e:
        return ToolResult(success=False, error=str(e))


def validate_sudoku(solution: List[List[int]]) -> ToolResult:
    try:
        is_valid = is_valid_solution(solution)
        return ToolResult(
            success=True,
            data={"is_valid": is_valid},
            metadata={"checked_at": datetime.now().isoformat()},
        )
    except Exception as e:
        return ToolResult(success=False, error=str(e))


def llm_play_sudoku(
    difficulty: str = "medium",
    provider: str = "ollama",
    model: str = None,
    mode: str = "step",
    api_key: str = None,
    verbose: bool = True,
) -> ToolResult:
    try:
        config = _providers.get(provider)
        if not config:
            return ToolResult(success=False, error=f"Unknown provider: {provider}")

        effective_api_key = api_key if api_key else config.api_key

        if model:
            config = LLMConfig(
                name=config.name,
                provider=config.provider,
                api_base=config.api_base,
                model=model,
                api_key=effective_api_key,
            )
        elif api_key:
            config = LLMConfig(
                name=config.name,
                provider=config.provider,
                api_base=config.api_base,
                model=config.model,
                api_key=effective_api_key,
            )

        gen_result = generate_sudoku(difficulty)
        if not gen_result.success:
            return gen_result

        game = SudokuGame.from_dict(gen_result.data)
        play_mode = PlayMode.STEP_BY_STEP if mode == "step" else PlayMode.ONE_SHOT

        result = play_game(game, config, play_mode, verbose=verbose)

        return ToolResult(
            success=True,
            data=result.to_dict(),
            metadata={
                "model": config.model,
                "mode": mode,
                "difficulty": difficulty,
            },
        )
    except Exception as e:
        return ToolResult(success=False, error=str(e))


def evaluate_llm(
    provider: str = "ollama",
    model: str = None,
    games_per_difficulty: int = 3,
    difficulties: List[str] = None,
    mode: str = "step",
    api_key: str = None,
    verbose: bool = True,
) -> ToolResult:
    try:
        config = _providers.get(provider)
        if not config:
            return ToolResult(success=False, error=f"Unknown provider: {provider}")

        effective_api_key = api_key if api_key else config.api_key

        if model:
            config = LLMConfig(
                name=config.name,
                provider=config.provider,
                api_base=config.api_base,
                model=model,
                api_key=effective_api_key,
            )
        elif api_key:
            config = LLMConfig(
                name=config.name,
                provider=config.provider,
                api_base=config.api_base,
                model=config.model,
                api_key=effective_api_key,
            )

        difficulties = difficulties or ["easy", "medium"]
        play_mode = PlayMode.STEP_BY_STEP if mode == "step" else PlayMode.ONE_SHOT

        result = evaluate_model(
            config,
            difficulties=difficulties,
            games_per_difficulty=games_per_difficulty,
            mode=play_mode,
            verbose=verbose,
        )

        return ToolResult(
            success=True,
            data=result.to_dict(),
            metadata={
                "model": config.model,
                "mode": mode,
                "difficulties": difficulties,
            },
        )
    except Exception as e:
        return ToolResult(success=False, error=str(e))


def generate_report(evaluation_json: str) -> ToolResult:
    try:
        data = json.loads(evaluation_json)
        result = EvaluationResult(
            model_name=data["model_name"],
            provider=data["provider"],
            total_games=data["total_games"],
            completed_games=data["completed_games"],
            correct_games=data["correct_games"],
            overall_accuracy=data["overall_accuracy"],
            total_time=data["total_time"],
            results_by_difficulty=data.get("results_by_difficulty", {}),
            play_results=[],
            evaluated_at=datetime.now(),
        )

        report = generate_evaluation_report(result)
        return ToolResult(
            success=True,
            data=report,
            metadata={"format": "markdown"},
        )
    except Exception as e:
        return ToolResult(success=False, error=str(e))


def list_llm_providers() -> ToolResult:
    return ToolResult(
        success=True,
        data={name: config.to_dict() for name, config in _providers.items()},
    )


def list_available_models(provider: str = "ollama") -> ToolResult:
    try:
        if provider == "ollama":
            from .llm.providers.ollama import OllamaProvider

            instance = OllamaProvider()
            models = instance.list_models()
        else:
            config = _providers.get(provider)
            if not config or not config.api_key:
                return ToolResult(
                    success=False, error=f"No API key configured for {provider}"
                )
            from .llm.providers.custom import CustomProvider

            instance = CustomProvider(
                api_base=config.api_base,
                model=config.model,
                api_key=config.api_key,
            )
            models = instance.list_models()

        return ToolResult(
            success=True,
            data={"provider": provider, "models": models},
            metadata={"count": len(models)},
        )
    except Exception as e:
        return ToolResult(success=False, error=str(e))


def add_llm_provider(
    name: str,
    provider: str,
    api_base: str,
    model: str,
    api_key: str = "",
) -> ToolResult:
    config = LLMConfig(
        name=name,
        provider=provider,
        api_base=api_base,
        model=model,
        api_key=api_key,
    )
    _providers[name] = config
    return ToolResult(
        success=True,
        data=config.to_dict(),
        metadata={"action": "added"},
    )


def dispatch(function_name: str, arguments: dict) -> ToolResult:
    handlers = {
        "generate_sudoku": lambda args: generate_sudoku(**args),
        "solve_sudoku": lambda args: solve_sudoku(**args),
        "validate_sudoku": lambda args: validate_sudoku(**args),
        "llm_play_sudoku": lambda args: llm_play_sudoku(**args),
        "evaluate_llm": lambda args: evaluate_llm(**args),
        "generate_report": lambda args: generate_report(**args),
    }

    handler = handlers.get(function_name)
    if not handler:
        return ToolResult(success=False, error=f"Unknown function: {function_name}")

    return handler(arguments)
