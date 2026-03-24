"""
Sudoku solver using backtracking algorithm.
"""

from __future__ import annotations

from typing import Optional
from .board import SudokuBoard


class SudokuSolver:
    """Solves Sudoku puzzles using backtracking."""

    @staticmethod
    def solve(board: SudokuBoard) -> Optional[SudokuBoard]:
        if SudokuSolver._solve_recursive(board):
            return board
        return None

    @staticmethod
    def _solve_recursive(board: SudokuBoard) -> bool:
        empty = board.get_empty_cells()
        if not empty:
            return True

        row, col = empty[0]
        possible = board.get_possible_values(row, col)

        for val in possible:
            board.set(row, col, val)
            if SudokuSolver._solve_recursive(board):
                return True
            board.clear(row, col)

        return False

    @staticmethod
    def get_hint(
        board: SudokuBoard, solution: SudokuBoard
    ) -> Optional[tuple[int, int, int]]:
        empty = board.get_empty_cells()
        if not empty:
            return None
        row, col = empty[0]
        return (row, col, solution.get(row, col))

    @staticmethod
    def count_solutions(board: SudokuBoard, max_count: int = 2) -> int:
        test_board = board.copy()
        return SudokuSolver._count_recursive(test_board, 0, max_count)

    @staticmethod
    def _count_recursive(board: SudokuBoard, count: int, max_count: int) -> int:
        if count >= max_count:
            return count

        empty = board.get_empty_cells()
        if not empty:
            return count + 1

        row, col = empty[0]
        possible = board.get_possible_values(row, col)

        for val in possible:
            board.set(row, col, val)
            count = SudokuSolver._count_recursive(board, count, max_count)
            if count >= max_count:
                return count
            board.clear(row, col)

        return count


def solve_puzzle(grid: list[list[int]]) -> Optional[list[list[int]]]:
    board = SudokuBoard(grid)
    solved = SudokuSolver.solve(board)
    return solved.grid if solved else None


def is_solvable(grid: list[list[int]]) -> bool:
    board = SudokuBoard(grid)
    return SudokuSolver.solve(board) is not None
