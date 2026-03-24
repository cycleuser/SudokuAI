"""
Tests for SudokuAI core modules.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sudokuai.sudoku.board import SudokuBoard
from sudokuai.sudoku.generator import SudokuGenerator
from sudokuai.sudoku.solver import SudokuSolver, solve_puzzle, is_solvable
from sudokuai.sudoku.validator import SudokuValidator, is_valid_solution


class TestSudokuBoard:
    def test_create_empty_board(self):
        board = SudokuBoard()
        assert board.count_clues() == 0

    def test_create_with_grid(self):
        grid = [[1 if i == j else 0 for j in range(9)] for i in range(9)]
        board = SudokuBoard(grid)
        assert board.count_clues() == 9

    def test_get_set(self):
        board = SudokuBoard()
        board.set(0, 0, 5)
        assert board.get(0, 0) == 5

    def test_get_empty_cells(self):
        board = SudokuBoard()
        empty = board.get_empty_cells()
        assert len(empty) == 81

    def test_get_possible_values(self):
        board = SudokuBoard()
        board.set(0, 0, 5)
        possible = board.get_possible_values(0, 1)
        assert 5 not in possible
        assert len(possible) == 8

    def test_copy(self):
        board1 = SudokuBoard()
        board1.set(0, 0, 5)
        board2 = board1.copy()
        board2.set(0, 1, 3)
        assert board1.get(0, 1) == 0
        assert board2.get(0, 1) == 3


class TestSudokuSolver:
    def test_solve_simple_puzzle(self):
        puzzle = [
            [5, 3, 0, 0, 7, 0, 0, 0, 0],
            [6, 0, 0, 1, 9, 5, 0, 0, 0],
            [0, 9, 8, 0, 0, 0, 0, 6, 0],
            [8, 0, 0, 0, 6, 0, 0, 0, 3],
            [4, 0, 0, 8, 0, 3, 0, 0, 1],
            [7, 0, 0, 0, 2, 0, 0, 0, 6],
            [0, 6, 0, 0, 0, 0, 2, 8, 0],
            [0, 0, 0, 4, 1, 9, 0, 0, 5],
            [0, 0, 0, 0, 8, 0, 0, 7, 9],
        ]
        solution = solve_puzzle(puzzle)
        assert solution is not None
        assert is_valid_solution(solution)

    def test_is_solvable(self):
        valid_puzzle = [[0] * 9 for _ in range(9)]
        valid_puzzle[0][0] = 1
        assert is_solvable(valid_puzzle)

    def test_count_solutions(self):
        puzzle = [[0] * 9 for _ in range(9)]
        count = SudokuSolver.count_solutions(SudokuBoard(puzzle), max_count=2)
        assert count >= 2


class TestSudokuValidator:
    def test_valid_solution(self):
        solution = [
            [5, 3, 4, 6, 7, 8, 9, 1, 2],
            [6, 7, 2, 1, 9, 5, 3, 4, 8],
            [1, 9, 8, 3, 4, 2, 5, 6, 7],
            [8, 5, 9, 7, 6, 1, 4, 2, 3],
            [4, 2, 6, 8, 5, 3, 7, 9, 1],
            [7, 1, 3, 9, 2, 4, 8, 5, 6],
            [9, 6, 1, 5, 3, 7, 2, 8, 4],
            [2, 8, 7, 4, 1, 9, 6, 3, 5],
            [3, 4, 5, 2, 8, 6, 1, 7, 9],
        ]
        assert is_valid_solution(solution)

    def test_invalid_solution_duplicate_row(self):
        solution = [
            [5, 5, 4, 6, 7, 8, 9, 1, 2],
            [6, 7, 2, 1, 9, 5, 3, 4, 8],
            [1, 9, 8, 3, 4, 2, 5, 6, 7],
            [8, 5, 9, 7, 6, 1, 4, 2, 3],
            [4, 2, 6, 8, 5, 3, 7, 9, 1],
            [7, 1, 3, 9, 2, 4, 8, 5, 6],
            [9, 6, 1, 5, 3, 7, 2, 8, 4],
            [2, 8, 7, 4, 1, 9, 6, 3, 5],
            [3, 4, 5, 2, 8, 6, 1, 7, 9],
        ]
        assert not is_valid_solution(solution)


class TestSudokuGenerator:
    def test_generate_easy(self):
        puzzle, solution = SudokuGenerator.create_puzzle("easy")
        assert puzzle.count_clues() >= 36
        assert puzzle.count_clues() <= 45

    def test_generate_medium(self):
        puzzle, solution = SudokuGenerator.create_puzzle("medium")
        assert puzzle.count_clues() >= 27
        assert puzzle.count_clues() <= 35

    def test_generate_hard(self):
        puzzle, solution = SudokuGenerator.create_puzzle("hard")
        assert puzzle.count_clues() >= 22
        assert puzzle.count_clues() <= 26

    def test_generated_puzzle_is_solvable(self):
        puzzle, solution = SudokuGenerator.create_puzzle("medium")
        assert is_solvable(puzzle.grid)

    def test_generated_solution_is_valid(self):
        puzzle, solution = SudokuGenerator.create_puzzle("medium")
        assert is_valid_solution(solution.grid)


class TestAPI:
    def test_generate_sudoku(self):
        from sudokuai.api import generate_sudoku

        result = generate_sudoku("easy")
        assert result.success
        assert "puzzle" in result.data
        assert "solution" in result.data

    def test_solve_sudoku(self):
        from sudokuai.api import solve_sudoku

        puzzle = [
            [5, 3, 0, 0, 7, 0, 0, 0, 0],
            [6, 0, 0, 1, 9, 5, 0, 0, 0],
            [0, 9, 8, 0, 0, 0, 0, 6, 0],
            [8, 0, 0, 0, 6, 0, 0, 0, 3],
            [4, 0, 0, 8, 0, 3, 0, 0, 1],
            [7, 0, 0, 0, 2, 0, 0, 0, 6],
            [0, 6, 0, 0, 0, 0, 2, 8, 0],
            [0, 0, 0, 4, 1, 9, 0, 0, 5],
            [0, 0, 0, 0, 8, 0, 0, 7, 9],
        ]
        result = solve_sudoku(puzzle)
        assert result.success
        assert is_valid_solution(result.data)

    def test_validate_sudoku(self):
        from sudokuai.api import validate_sudoku

        solution = [
            [5, 3, 4, 6, 7, 8, 9, 1, 2],
            [6, 7, 2, 1, 9, 5, 3, 4, 8],
            [1, 9, 8, 3, 4, 2, 5, 6, 7],
            [8, 5, 9, 7, 6, 1, 4, 2, 3],
            [4, 2, 6, 8, 5, 3, 7, 9, 1],
            [7, 1, 3, 9, 2, 4, 8, 5, 6],
            [9, 6, 1, 5, 3, 7, 2, 8, 4],
            [2, 8, 7, 4, 1, 9, 6, 3, 5],
            [3, 4, 5, 2, 8, 6, 1, 7, 9],
        ]
        result = validate_sudoku(solution)
        assert result.success
        assert result.data["is_valid"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
