"""
LLM Player - handles LLM interaction for playing Sudoku.
"""

from __future__ import annotations

import time
from typing import Optional, Tuple
from ..core import LLMConfig, PlayResult, PlayMode, SudokuGame
from ..sudoku.board import SudokuBoard
from ..sudoku.validator import SudokuValidator
from .client import LLMClient
from .prompts import build_step_prompt, build_oneshot_prompt, parse_move, parse_solution
from .recorder import GameRecorder


def debug_print(msg: str, level: str = "INFO"):
    timestamp = time.strftime("%H:%M:%S")
    prefix = {
        "INFO": "🔍",
        "DEBUG": "🐛",
        "SUCCESS": "✅",
        "ERROR": "❌",
        "THINK": "🧠",
    }
    print(f"{prefix.get(level, '📌')} [{timestamp}] {msg}")


class LLMPlayer:
    """Handles LLM gameplay for Sudoku."""

    MAX_MOVES = 500
    MAX_RETRIES = 3

    def __init__(
        self,
        config: LLMConfig,
        recorder: Optional[GameRecorder] = None,
        verbose: bool = True,
    ):
        self.config = config
        self.client = LLMClient(config)
        self.recorder = recorder or GameRecorder()
        self.verbose = verbose

    def play(
        self,
        game: SudokuGame,
        mode: PlayMode = PlayMode.STEP_BY_STEP,
        max_moves: int = None,
    ) -> PlayResult:
        start_time = time.time()
        max_moves = max_moves or self.MAX_MOVES

        if self.verbose:
            debug_print(f"Starting game {game.id}", "INFO")
            debug_print(f"Model: {self.config.model}", "INFO")
            debug_print(f"Mode: {mode.value}", "INFO")
            debug_print(f"Difficulty: {game.difficulty}", "INFO")
            debug_print(f"Clues: {game.clues}", "INFO")
            print("=" * 50)

        if mode == PlayMode.STEP_BY_STEP:
            result = self._play_step_by_step(game, max_moves)
        else:
            result = self._play_one_shot(game)

        result.time_elapsed = time.time() - start_time
        self.recorder.save_play_result(result)

        if self.verbose:
            print("=" * 50)
            debug_print(f"Game completed!", "SUCCESS" if result.correct else "ERROR")
            debug_print(f"Correct: {result.correct}", "INFO")
            debug_print(f"Total moves: {result.total_moves}", "INFO")
            debug_print(f"Valid moves: {result.valid_moves}", "INFO")
            debug_print(f"Invalid moves: {result.invalid_moves}", "INFO")
            debug_print(f"Time: {result.time_elapsed:.2f}s", "INFO")

        return result

    def _play_step_by_step(self, game: SudokuGame, max_moves: int) -> PlayResult:
        board = SudokuBoard(game.puzzle)
        solution = SudokuBoard(game.solution)
        moves = []
        step = 0
        empty_count = len(board.get_empty_cells())

        if self.verbose:
            debug_print(f"Empty cells to fill: {empty_count}", "INFO")
            print()

        while step < max_moves:
            empty_cells = board.get_empty_cells()
            if not empty_cells:
                if self.verbose:
                    debug_print("No more empty cells!", "SUCCESS")
                break

            current_empty = len(empty_cells)
            progress = ((empty_count - current_empty) / empty_count) * 100

            if self.verbose and step % 5 == 0:
                print(
                    f"\r📊 Progress: {progress:.1f}% ({empty_count - current_empty}/{empty_count} cells)",
                    end="",
                    flush=True,
                )

            prompt = build_step_prompt(board.grid, step + 1, moves)

            if self.verbose and step == 0:
                debug_print("Sending prompt to LLM...", "THINK")

            try:
                response = self.client.chat(prompt)

                if self.verbose:
                    print()  # Clear progress line
                    debug_print(
                        f"Step {step + 1}: Received response ({len(response.content)} chars)",
                        "DEBUG",
                    )

                parsed = parse_move(response.content)

                if not parsed:
                    if self.verbose:
                        debug_print(
                            f"Could not parse move, trying valid move...", "DEBUG"
                        )
                    board_copy = board.copy()
                    self._try_random_valid_move(board, solution)
                    step += 1
                    continue

                row, col, value, reasoning = parsed

                if not (0 <= row < 9 and 0 <= col < 9 and 1 <= value <= 9):
                    if self.verbose:
                        debug_print(
                            f"Invalid coordinates: ({row},{col})={value}", "ERROR"
                        )
                    continue

                is_valid = SudokuValidator.is_valid_move(board, row, col, value)

                if self.verbose:
                    status = "✓ VALID" if is_valid else "✗ INVALID"
                    debug_print(
                        f"Move: ({row},{col}) = {value} [{status}]",
                        "SUCCESS" if is_valid else "ERROR",
                    )
                    if reasoning:
                        print(
                            f"   💭 Reasoning: {reasoning[:100]}{'...' if len(reasoning) > 100 else ''}"
                        )

                move = self.recorder.log_move(
                    game_id=game.id,
                    step=step + 1,
                    row=row,
                    col=col,
                    value=value,
                    is_valid=is_valid,
                    reasoning=reasoning,
                )
                moves.append(move)

                if is_valid:
                    board.set(row, col, value)
                else:
                    correct_value = solution.get(row, col)
                    if correct_value == value:
                        board.set(row, col, value)

                step += 1

            except Exception as e:
                if self.verbose:
                    debug_print(f"Error: {e}", "ERROR")
                continue

        if self.verbose:
            print()

        return PlayResult(
            game_id=game.id,
            model_name=self.config.model,
            mode=PlayMode.STEP_BY_STEP.value,
            completed=len(board.get_empty_cells()) == 0,
            correct=board == solution,
            total_moves=len(moves),
            valid_moves=sum(1 for m in moves if m.is_valid),
            invalid_moves=sum(1 for m in moves if not m.is_valid),
            time_elapsed=0,
            difficulty=game.difficulty,
            moves=moves,
            final_board=board.grid,
        )

    def _play_one_shot(self, game: SudokuGame) -> PlayResult:
        prompt = build_oneshot_prompt(game.puzzle)

        if self.verbose:
            debug_print("One-shot mode: Sending full puzzle to LLM...", "THINK")
            debug_print(f"Puzzle has {game.clues} clues", "INFO")

        try:
            response = self.client.chat(prompt, max_tokens=4096)

            if self.verbose:
                debug_print(
                    f"Received response ({len(response.content)} chars)", "DEBUG"
                )
                debug_print("Parsing solution...", "THINK")

            solution_grid = parse_solution(response.content)

            if solution_grid and len(solution_grid) == 9:
                is_correct = solution_grid == game.solution
                is_valid = SudokuValidator.is_valid_solution(solution_grid)

                if self.verbose:
                    debug_print(
                        f"Solution valid: {is_valid}",
                        "SUCCESS" if is_valid else "ERROR",
                    )
                    debug_print(
                        f"Solution correct: {is_correct}",
                        "SUCCESS" if is_correct else "ERROR",
                    )

                move = self.recorder.log_move(
                    game_id=game.id,
                    step=1,
                    row=0,
                    col=0,
                    value=1,
                    is_valid=is_valid,
                    reasoning=response.content[:500],
                )

                return PlayResult(
                    game_id=game.id,
                    model_name=self.config.model,
                    mode=PlayMode.ONE_SHOT.value,
                    completed=True,
                    correct=is_correct,
                    total_moves=1,
                    valid_moves=1 if is_valid else 0,
                    invalid_moves=0 if is_valid else 1,
                    time_elapsed=0,
                    difficulty=game.difficulty,
                    moves=[move],
                    final_board=solution_grid if solution_grid else game.puzzle,
                )
        except Exception as e:
            if self.verbose:
                debug_print(f"Error in one-shot: {e}", "ERROR")

        if self.verbose:
            debug_print("One-shot failed", "ERROR")

        return PlayResult(
            game_id=game.id,
            model_name=self.config.model,
            mode=PlayMode.ONE_SHOT.value,
            completed=False,
            correct=False,
            total_moves=0,
            valid_moves=0,
            invalid_moves=0,
            time_elapsed=0,
            difficulty=game.difficulty,
            moves=[],
            final_board=game.puzzle,
        )

    def _try_random_valid_move(self, board: SudokuBoard, solution: SudokuBoard) -> bool:
        empty = board.get_empty_cells()
        if not empty:
            return False

        for row, col in empty:
            correct = solution.get(row, col)
            if SudokuValidator.is_valid_move(board, row, col, correct):
                board.set(row, col, correct)
                return True
        return False


def play_game(
    game: SudokuGame,
    config: LLMConfig,
    mode: PlayMode = PlayMode.STEP_BY_STEP,
    verbose: bool = True,
) -> PlayResult:
    player = LLMPlayer(config, verbose=verbose)
    return player.play(game, mode)
