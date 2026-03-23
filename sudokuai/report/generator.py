"""
Report generator for evaluation results.
"""

from typing import List, Dict
from datetime import datetime

from ..core import EvaluationResult, PlayResult
from .templates import REPORT_TEMPLATE, DIFFICULTY_ROW_TEMPLATE, COMPARISON_TEMPLATE


def generate_evaluation_report(result: EvaluationResult, version: str = "1.0.0") -> str:
    difficulty_rows = []
    for difficulty, stats in result.results_by_difficulty.items():
        difficulty_results = [r for r in result.play_results if r.difficulty == difficulty]
        avg_moves = sum(r.total_moves for r in difficulty_results) / len(difficulty_results) if difficulty_results else 0
        avg_invalid = sum(r.invalid_moves for r in difficulty_results) / len(difficulty_results) if difficulty_results else 0
        
        row = DIFFICULTY_ROW_TEMPLATE.format(
            difficulty=difficulty.capitalize(),
            total=stats["total"],
            completed=stats["completed"],
            correct=stats["correct"],
            accuracy=stats["accuracy"],
            avg_moves=avg_moves,
            avg_invalid=avg_invalid,
        )
        difficulty_rows.append(row)
    
    total_moves = sum(r.total_moves for r in result.play_results)
    valid_moves = sum(r.valid_moves for r in result.play_results)
    invalid_moves = sum(r.invalid_moves for r in result.play_results)
    valid_rate = valid_moves / total_moves if total_moves > 0 else 0
    invalid_rate = invalid_moves / total_moves if total_moves > 0 else 0
    
    avg_time = result.total_time / result.total_games if result.total_games > 0 else 0
    avg_moves_per_game = total_moves / result.total_games if result.total_games > 0 else 0
    
    difficulties_tested = ", ".join(result.results_by_difficulty.keys())
    games_per_difficulty = list(result.results_by_difficulty.values())[0]["total"] if result.results_by_difficulty else 0
    
    play_mode = result.play_results[0].mode if result.play_results else "unknown"
    
    if result.overall_accuracy >= 0.8:
        conclusions = f"{result.model_name} demonstrates strong Sudoku solving capability with {result.overall_accuracy:.1%} accuracy."
    elif result.overall_accuracy >= 0.5:
        conclusions = f"{result.model_name} shows moderate Sudoku solving ability with room for improvement."
    else:
        conclusions = f"{result.model_name} struggles with Sudoku puzzles, suggesting limitations in logical reasoning."
    
    return REPORT_TEMPLATE.format(
        model_name=result.model_name,
        provider=result.provider,
        evaluated_at=result.evaluated_at.strftime("%Y-%m-%d %H:%M:%S"),
        total_games=result.total_games,
        completed_games=result.completed_games,
        correct_games=result.correct_games,
        overall_accuracy=result.overall_accuracy,
        total_time=result.total_time,
        difficulty_table="\n".join(difficulty_rows),
        total_moves=total_moves,
        valid_moves=valid_moves,
        valid_rate=valid_rate,
        invalid_moves=invalid_moves,
        invalid_rate=invalid_rate,
        avg_time_per_game=avg_time,
        avg_moves_per_game=avg_moves_per_game,
        play_mode=play_mode,
        difficulties_tested=difficulties_tested,
        games_per_difficulty=games_per_difficulty,
        conclusions=conclusions,
        version=version,
    )


def generate_comparison_report(
    result1: EvaluationResult,
    result2: EvaluationResult,
    version: str = "1.0.0",
) -> str:
    comparison_rows = []
    all_difficulties = set(result1.results_by_difficulty.keys()) | set(result2.results_by_difficulty.keys())
    
    for difficulty in sorted(all_difficulties):
        stats1 = result1.results_by_difficulty.get(difficulty, {"accuracy": 0})
        stats2 = result2.results_by_difficulty.get(difficulty, {"accuracy": 0})
        
        acc1 = stats1.get("accuracy", 0)
        acc2 = stats2.get("accuracy", 0)
        
        if acc1 > acc2:
            winner = result1.model_name
        elif acc2 > acc1:
            winner = result2.model_name
        else:
            winner = "Tie"
        
        comparison_rows.append(
            f"| {difficulty.capitalize()} | {acc1:.1%} | {acc2:.1%} | {winner} |"
        )
    
    if result1.overall_accuracy > result2.overall_accuracy:
        analysis = f"{result1.model_name} outperforms {result2.model_name} overall."
    elif result2.overall_accuracy > result1.overall_accuracy:
        analysis = f"{result2.model_name} outperforms {result1.model_name} overall."
    else:
        analysis = "Both models perform equally overall."
    
    return COMPARISON_TEMPLATE.format(
        model1_name=result1.model_name,
        model2_name=result2.model_name,
        model1_accuracy=result1.overall_accuracy,
        model2_accuracy=result2.overall_accuracy,
        model1_games=result1.total_games,
        model2_games=result2.total_games,
        model1_correct=result1.correct_games,
        model2_correct=result2.correct_games,
        model1_time=result1.total_time,
        model2_time=result2.total_time,
        comparison_table="\n".join(comparison_rows),
        analysis=analysis,
        version=version,
    )