"""
Sudoku puzzle generator with difficulty levels.
"""

from __future__ import annotations

import random
from typing import Optional, Tuple
from .board import SudokuBoard
from .solver import SudokuSolver


class SudokuGenerator:
    """Generates Sudoku puzzles with specified difficulty."""

    DIFFICULTY_CONFIG = {
        "easy": {"clues_range": (36, 45), "max_attempts": 5},
        "medium": {"clues_range": (27, 35), "max_attempts": 10},
        "hard": {"clues_range": (22, 26), "max_attempts": 15},
        "expert": {"clues_range": (17, 21), "max_attempts": 25},
        "master": {"clues_range": (14, 16), "max_attempts": 40},
    }

    @staticmethod
    def generate_filled_board() -> SudokuBoard:
        board = SudokuBoard()
        numbers = list(range(1, 10))

        def fill(pos: int) -> bool:
            if pos == 81:
                return True

            row, col = pos // 9, pos % 9
            random.shuffle(numbers)

            for num in numbers:
                possible = board.get_possible_values(row, col)
                if num in possible:
                    board.set(row, col, num)
                    if fill(pos + 1):
                        return True
                    board.clear(row, col)

            return False

        fill(0)
        return board

    @staticmethod
    def create_puzzle(difficulty: str = "medium") -> Tuple[SudokuBoard, SudokuBoard]:
        config = SudokuGenerator.DIFFICULTY_CONFIG.get(difficulty, 
                                                        SudokuGenerator.DIFFICULTY_CONFIG["medium"])
        min_clues, max_clues = config["clues_range"]
        target_clues = random.randint(min_clues, max_clues)

        solution = SudokuGenerator.generate_filled_board()
        puzzle = solution.copy()

        cells = [(r, c) for r in range(9) for c in range(9)]
        random.shuffle(cells)

        removed = 0
        to_remove = 81 - target_clues

        for row, col in cells:
            if removed >= to_remove:
                break

            original = puzzle.get(row, col)
            puzzle.clear(row, col)

            if SudokuSolver.count_solutions(puzzle, 2) == 1:
                removed += 1
            else:
                puzzle.set(row, col, original)

        return puzzle, solution

    @staticmethod
    def generate_game(difficulty: str = "medium") -> dict:
        puzzle, solution = SudokuGenerator.create_puzzle(difficulty)
        return {
            "puzzle": puzzle.grid,
            "solution": solution.grid,
            "difficulty": difficulty,
            "clues": puzzle.count_clues(),
        }


def generate_puzzle(difficulty: str = "medium") -> Tuple[list[list[int]], list[list[int]]]:
    puzzle, solution = SudokuGenerator.create_puzzle(difficulty)
    return puzzle.grid, solution.grid