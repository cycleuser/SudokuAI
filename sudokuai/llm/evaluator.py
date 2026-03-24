"""
LLM Evaluator - batch evaluation of LLM performance on Sudoku.
"""

from __future__ import annotations

import time
from typing import List, Dict, Optional
from datetime import datetime

from ..core import LLMConfig, EvaluationResult, PlayResult, PlayMode, SudokuGame
from ..sudoku.generator import SudokuGenerator
from .player import LLMPlayer, debug_print


class LLMEvaluator:
    """Evaluates LLM performance on multiple Sudoku games."""

    DEFAULT_DIFFICULTIES = ["easy", "medium", "hard"]
    DEFAULT_GAMES_PER_DIFFICULTY = 3

    def __init__(self, config: LLMConfig, verbose: bool = True):
        self.config = config
        self.verbose = verbose
        self.player = LLMPlayer(config, verbose=False)

    def evaluate(
        self,
        difficulties: List[str] = None,
        games_per_difficulty: int = None,
        mode: PlayMode = PlayMode.STEP_BY_STEP,
        max_moves: int = 200,
    ) -> EvaluationResult:
        difficulties = difficulties or self.DEFAULT_DIFFICULTIES
        games_per_difficulty = games_per_difficulty or self.DEFAULT_GAMES_PER_DIFFICULTY

        all_results: List[PlayResult] = []
        results_by_difficulty: Dict[str, Dict] = {}

        start_time = time.time()
        total_games = len(difficulties) * games_per_difficulty
        game_count = 0

        if self.verbose:
            print("\n" + "=" * 50)
            debug_print(f"Starting Evaluation", "INFO")
            debug_print(f"Model: {self.config.model}", "INFO")
            debug_print(f"Provider: {self.config.provider}", "INFO")
            debug_print(f"Mode: {mode.value}", "INFO")
            debug_print(f"Games per difficulty: {games_per_difficulty}", "INFO")
            debug_print(f"Difficulties: {', '.join(difficulties)}", "INFO")
            debug_print(f"Total games: {total_games}", "INFO")
            print("=" * 50 + "\n")

        for difficulty in difficulties:
            difficulty_results: List[PlayResult] = []
            correct = 0
            completed = 0

            if self.verbose:
                debug_print(f"Testing difficulty: {difficulty.upper()}", "THINK")

            for i in range(games_per_difficulty):
                game_count += 1
                game_id = f"{difficulty}_{i+1}"

                if self.verbose:
                    progress = (game_count / total_games) * 100
                    print(
                        f"\r📊 Overall progress: {progress:.1f}% | Game {game_count}/{total_games} ({difficulty} #{i+1})",
                        end="",
                        flush=True,
                    )

                game_data = SudokuGenerator.generate_game(difficulty)
                game = SudokuGame(
                    id=game_id,
                    puzzle=game_data["puzzle"],
                    solution=game_data["solution"],
                    difficulty=difficulty,
                    clues=game_data["clues"],
                )

                try:
                    result = self.player.play(game, mode, max_moves)
                    difficulty_results.append(result)
                    all_results.append(result)

                    if result.completed:
                        completed += 1
                    if result.correct:
                        correct += 1

                except Exception as e:
                    if self.verbose:
                        print()
                        debug_print(f"Error in game {game_id}: {e}", "ERROR")
                    continue

            if self.verbose:
                print()  # Clear progress line
                accuracy = (
                    correct / games_per_difficulty if games_per_difficulty > 0 else 0
                )
                debug_print(
                    f"{difficulty.upper()}: {correct}/{games_per_difficulty} correct ({accuracy:.0%})",
                    "SUCCESS" if accuracy >= 0.5 else "ERROR",
                )

            results_by_difficulty[difficulty] = {
                "total": games_per_difficulty,
                "completed": completed,
                "correct": correct,
                "accuracy": (
                    correct / games_per_difficulty if games_per_difficulty > 0 else 0
                ),
            }

        total_time = time.time() - start_time
        total_games_actual = len(all_results)
        completed_games = sum(1 for r in all_results if r.completed)
        correct_games = sum(1 for r in all_results if r.correct)
        overall_accuracy = (
            correct_games / total_games_actual if total_games_actual > 0 else 0
        )

        if self.verbose:
            print("\n" + "=" * 50)
            debug_print("Evaluation Complete!", "SUCCESS")
            debug_print(f"Total time: {total_time:.1f}s", "INFO")
            debug_print(
                f"Overall accuracy: {overall_accuracy:.1%}",
                "SUCCESS" if overall_accuracy >= 0.5 else "ERROR",
            )
            debug_print(f"Correct: {correct_games}/{total_games_actual}", "INFO")
            print("=" * 50 + "\n")

        return EvaluationResult(
            model_name=self.config.model,
            provider=self.config.provider,
            total_games=total_games_actual,
            completed_games=completed_games,
            correct_games=correct_games,
            overall_accuracy=overall_accuracy,
            total_time=total_time,
            results_by_difficulty=results_by_difficulty,
            play_results=all_results,
            evaluated_at=datetime.now(),
        )


def evaluate_model(
    config: LLMConfig,
    difficulties: List[str] = None,
    games_per_difficulty: int = None,
    mode: PlayMode = PlayMode.STEP_BY_STEP,
    verbose: bool = True,
) -> EvaluationResult:
    evaluator = LLMEvaluator(config, verbose=verbose)
    return evaluator.evaluate(difficulties, games_per_difficulty, mode)
