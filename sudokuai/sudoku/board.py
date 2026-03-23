"""
Sudoku board data structure and operations.
"""

from __future__ import annotations

from typing import Optional
import copy


class SudokuBoard:
    """Represents a 9x9 Sudoku board."""

    SIZE = 9
    EMPTY = 0

    def __init__(self, grid: Optional[list[list[int]]] = None):
        if grid is None:
            self._grid = [[self.EMPTY] * self.SIZE for _ in range(self.SIZE)]
        else:
            self._grid = [row[:] for row in grid]

    @property
    def grid(self) -> list[list[int]]:
        return [row[:] for row in self._grid]

    def get(self, row: int, col: int) -> int:
        return self._grid[row][col]

    def set(self, row: int, col: int, value: int) -> None:
        self._grid[row][col] = value

    def clear(self, row: int, col: int) -> None:
        self._grid[row][col] = self.EMPTY

    def is_empty(self, row: int, col: int) -> bool:
        return self._grid[row][col] == self.EMPTY

    def get_empty_cells(self) -> list[tuple[int, int]]:
        return [(r, c) for r in range(self.SIZE) for c in range(self.SIZE) 
                if self._grid[r][c] == self.EMPTY]

    def get_possible_values(self, row: int, col: int) -> set[int]:
        if not self.is_empty(row, col):
            return set()

        used = set()

        for c in range(self.SIZE):
            if self._grid[row][c] != self.EMPTY:
                used.add(self._grid[row][c])

        for r in range(self.SIZE):
            if self._grid[r][col] != self.EMPTY:
                used.add(self._grid[r][col])

        box_row, box_col = 3 * (row // 3), 3 * (col // 3)
        for r in range(box_row, box_row + 3):
            for c in range(box_col, box_col + 3):
                if self._grid[r][c] != self.EMPTY:
                    used.add(self._grid[r][c])

        return set(range(1, 10)) - used

    def count_clues(self) -> int:
        return sum(1 for r in range(self.SIZE) for c in range(self.SIZE) 
                   if self._grid[r][c] != self.EMPTY)

    def copy(self) -> "SudokuBoard":
        return SudokuBoard(self._grid)

    def to_string(self) -> str:
        return "".join(str(self._grid[r][c]) for r in range(self.SIZE) for c in range(self.SIZE))

    @classmethod
    def from_string(cls, s: str) -> "SudokuBoard":
        grid = [[int(s[r * 9 + c]) for c in range(cls.SIZE)] for r in range(cls.SIZE)]
        return cls(grid)

    def __str__(self) -> str:
        lines = []
        for i, row in enumerate(self._grid):
            if i % 3 == 0 and i != 0:
                lines.append("-" * 21)
            line = []
            for j, val in enumerate(row):
                if j % 3 == 0 and j != 0:
                    line.append("|")
                line.append(str(val) if val != self.EMPTY else ".")
            lines.append(" ".join(line))
        return "\n".join(lines)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SudokuBoard):
            return False
        return self._grid == other._grid