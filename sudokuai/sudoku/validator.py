"""
Sudoku validation utilities.
"""

from typing import List
from .board import SudokuBoard


class SudokuValidator:
    """Validates Sudoku solutions and moves."""

    @staticmethod
    def is_valid_grid(grid: List[List[int]]) -> bool:
        if len(grid) != 9:
            return False
        for row in grid:
            if len(row) != 9:
                return False
            for val in row:
                if not isinstance(val, int) or val < 0 or val > 9:
                    return False
        return True

    @staticmethod
    def is_valid_move(board: SudokuBoard, row: int, col: int, value: int) -> bool:
        if value < 1 or value > 9:
            return False
        if not board.is_empty(row, col):
            return False
        return value in board.get_possible_values(row, col)

    @staticmethod
    def is_valid_solution(grid: List[List[int]]) -> bool:
        if not SudokuValidator.is_valid_grid(grid):
            return False

        for r in range(9):
            if len(set(grid[r])) != 9:
                return False

        for c in range(9):
            col_vals = [grid[r][c] for r in range(9)]
            if len(set(col_vals)) != 9:
                return False

        for box_row in range(3):
            for box_col in range(3):
                box_vals = []
                for r in range(3):
                    for c in range(3):
                        box_vals.append(grid[box_row * 3 + r][box_col * 3 + c])
                if len(set(box_vals)) != 9:
                    return False

        return True

    @staticmethod
    def is_complete(grid: List[List[int]]) -> bool:
        if not SudokuValidator.is_valid_grid(grid):
            return False
        for row in grid:
            if 0 in row:
                return False
        return SudokuValidator.is_valid_solution(grid)

    @staticmethod
    def compare_solutions(solution1: List[List[int]], solution2: List[List[int]]) -> bool:
        return solution1 == solution2


def is_valid_solution(grid: List[List[int]]) -> bool:
    return SudokuValidator.is_valid_solution(grid)


def is_valid_move(board: SudokuBoard, row: int, col: int, value: int) -> bool:
    return SudokuValidator.is_valid_move(board, row, col, value)