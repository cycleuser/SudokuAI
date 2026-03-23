# AGENTS.md

This document provides guidance for agentic coding agents working on the SudokuAI codebase.

## Project Overview

SudokuAI is a Sudoku game platform for LLM evaluation. It provides puzzle generation, multiple difficulty levels, and comprehensive LLM performance benchmarking through CLI, GUI (PySide6), and Web (Flask) interfaces.

## Build/Lint/Test Commands

### Installation

```bash
pip install -e .                    # Install in development mode
pip install -e ".[dev]"             # Install with dev dependencies
```

### Testing

```bash
pytest                              # Run all tests
pytest -v                           # Run tests with verbose output
pytest tests/test_core.py           # Run a single test file
pytest tests/test_core.py::TestSudokuBoard::test_create_empty_board  # Run a single test
pytest -k "board"                   # Run tests matching keyword
pytest --tb=short                   # Short traceback format
```

### Linting and Formatting

```bash
black sudokuai tests                # Format code with black
black --check sudokuai tests        # Check formatting without modifying
mypy sudokuai                       # Type check with mypy
```

### Running the Application

```bash
sudokuai                            # Launch GUI (default)
sudokuai gui                        # Explicit GUI mode
sudokuai web --port 5000            # Start web server
sudokuai generate -d medium         # Generate a puzzle
sudokuai play -m gemma3:4b -d easy  # Have LLM play a game
sudokuai evaluate -m gemma3:4b      # Evaluate LLM performance
```

## Code Style Guidelines

### Imports

```python
# Standard library imports first (alphabetically)
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Any
import json

# Third-party imports second
from openai import OpenAI
from PySide6.QtWidgets import QWidget

# Local imports last (use relative imports within package)
from .core import ToolResult, SudokuGame
from ..sudoku.board import SudokuBoard
```

- Use `from __future__ import annotations` at the top for modern type hints
- Use relative imports within the package (`.` for same directory, `..` for parent)
- Group imports: standard library, third-party, local (separated by blank lines)

### Formatting

- Use **black** for code formatting (line length 88 by default)
- Use 4 spaces for indentation
- Maximum line length: 88 characters (black default)
- Use double quotes for strings
- Use trailing commas in multi-line collections

### Type Hints

```python
# Use Python 3.9+ style lowercase generics
def get_empty_cells(self) -> list[tuple[int, int]]: ...
def solve_puzzle(grid: list[list[int]]) -> Optional[list[list[int]]]: ...

# Use Optional for optional parameters/returns
def get(self, row: int, col: int) -> int: ...

# Use dataclass field for mutable defaults
from dataclasses import dataclass, field

@dataclass
class PlayResult:
    moves: list[GameMove] = field(default_factory=list)
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Modules | snake_case | `sudoku_board.py` |
| Classes | PascalCase | `SudokuBoard`, `LLMPlayer` |
| Functions | snake_case | `solve_puzzle()`, `play_game()` |
| Variables | snake_case | `empty_cells`, `current_board` |
| Constants | UPPER_SNAKE_CASE | `MAX_MOVES`, `EMPTY`, `SIZE` |
| Private methods | _leading_underscore | `_solve_recursive()`, `_create_provider()` |
| Class attributes | UPPER_SNAKE_CASE for constants | `SIZE = 9`, `EMPTY = 0` |

### Data Classes

Use `@dataclass` for data structures:

```python
@dataclass
class ToolResult:
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
        }
```

### Error Handling

Use `ToolResult` for API-level error handling:

```python
def generate_sudoku(difficulty: str = "medium") -> ToolResult:
    try:
        game_data = SudokuGenerator.generate_game(difficulty)
        return ToolResult(
            success=True,
            data=game.to_dict(),
            metadata={"difficulty": difficulty},
        )
    except Exception as e:
        return ToolResult(success=False, error=str(e))
```

- Wrap public API functions with try/except
- Return `ToolResult` with `success=False` and error message
- Use specific exceptions when possible
- Log errors with descriptive messages

### Module Structure

```python
"""
Module docstring describing the purpose.
"""

from __future__ import annotations

# Standard library imports
from typing import Optional
import json

# Third-party imports
# (if any)

# Local imports
from .board import SudokuBoard

# Constants
MAX_MOVES = 500

# Classes
class SudokuSolver:
    """Class docstring."""
    
    @staticmethod
    def solve(board: SudokuBoard) -> Optional[SudokuBoard]:
        ...

# Public functions
def solve_puzzle(grid: list[list[int]]) -> Optional[list[list[int]]]:
    ...

# Private helper functions
def _helper_function():
    ...

if __name__ == "__main__":
    main()
```

### Enums

```python
from enum import Enum

class Difficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class PlayMode(Enum):
    STEP_BY_STEP = "step"
    ONE_SHOT = "oneshot"
```

### Properties and Methods

```python
class SudokuBoard:
    SIZE = 9  # Class constant
    EMPTY = 0

    def __init__(self, grid: Optional[list[list[int]]] = None):
        self._grid = grid or [[self.EMPTY] * self.SIZE for _ in range(self.SIZE)]

    @property
    def grid(self) -> list[list[int]]:
        return [row[:] for row in self._grid]

    def get(self, row: int, col: int) -> int:
        return self._grid[row][col]

    def copy(self) -> "SudokuBoard":
        return SudokuBoard(self._grid)
```

### Testing

```python
"""
Tests for SudokuAI core modules.
"""

import pytest
from sudokuai.sudoku.board import SudokuBoard


class TestSudokuBoard:
    def test_create_empty_board(self):
        board = SudokuBoard()
        assert board.count_clues() == 0

    def test_get_set(self):
        board = SudokuBoard()
        board.set(0, 0, 5)
        assert board.get(0, 0) == 5
```

- Use pytest for all tests
- Group tests in classes by module/functionality
- Use descriptive test names starting with `test_`
- Use `pytest` fixtures in `conftest.py` for shared setup

## Project Structure

```
sudokuai/
├── __init__.py          # Package exports and version
├── __main__.py          # Entry point for python -m sudokuai
├── core.py              # Core data structures (ToolResult, dataclasses)
├── api.py               # Unified API with OpenAI-style tools
├── cli.py               # Command-line interface
├── gui.py               # PySide6 GUI
├── app.py               # Flask web application
├── sudoku/              # Sudoku game logic
│   ├── board.py         # Board data structure
│   ├── generator.py     # Puzzle generation
│   ├── solver.py        # Backtracking solver
│   └── validator.py     # Solution validation
├── llm/                 # LLM integration
│   ├── client.py        # Unified LLM client
│   ├── player.py        # LLM gameplay logic
│   ├── evaluator.py     # Model evaluation
│   ├── prompts.py       # Prompt templates
│   ├── recorder.py      # Game recording
│   └── providers/       # Provider implementations
│       ├── base.py      # Abstract base class
│       └── ollama.py    # Ollama provider
└── report/              # Report generation
    └── generator.py     # Markdown reports
```

## Key Patterns

### ToolResult Pattern

All public API functions return `ToolResult`:

```python
result = generate_sudoku("easy")
if result.success:
    game = result.data
    print(f"Generated game with {result.metadata['clues']} clues")
else:
    print(f"Error: {result.error}")
```

### LLM Configuration

```python
from sudokuai.core import LLMConfig

config = LLMConfig(
    name="ollama",
    provider="ollama",
    api_base="http://localhost:11434/v1",
    model="gemma3:4b",
    api_key="ollama",
)
```

### Factory Functions

```python
def create_client(config: LLMConfig) -> LLMClient:
    return LLMClient(config)
```

## GUI Features

The GUI (`sudokuai/gui.py`) provides an interactive interface with:

### Animated Step-by-Step Gameplay
- `SudokuCell`: Individual cell with animated value placement
- `SudokuGridWidget`: Full 9x9 grid with proper 3x3 box borders
- Highlight animations for valid (green) and invalid (red) moves
- Shake animation on invalid moves
- Conflict highlighting (shows conflicting cells in yellow)

### Thought Bubbles
- `ThoughtBubble`: Displays AI reasoning for each move
- Color-coded: green (valid), red (invalid), yellow (thinking)
- `ThoughtBubbleContainer`: Scrollable container for recent thoughts

### Toast Notifications
- `ToastWidget`: Non-blocking notifications
- `show_error()`: Red error messages
- `show_warning()`: Orange warnings
- `show_success()`: Green success messages

### Playback Controls
- Play/Pause/Stop buttons
- Speed slider (100ms - 3000ms per move)
- Progress bar showing completion percentage

### Error Feedback to LLM
When the LLM makes an invalid move:
1. Error is displayed visually (red highlight, shake, toast)
2. Error details are added to thought bubble
3. Next prompt includes error feedback so LLM can learn
4. `build_error_feedback_prompt()` provides detailed correction hints

## Dependencies

- **Python**: 3.10+
- **Core**: openai, PySide6, Flask, requests
- **Dev**: pytest, black, mypy