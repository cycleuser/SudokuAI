"""
Graphical user interface for SudokuAI using PySide6.
"""

import sys
from datetime import datetime
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QLabel, QLineEdit, QComboBox,
    QSpinBox, QGroupBox, QTableWidget, QTableWidgetItem,
    QTabWidget, QTextEdit, QStatusBar, QMenuBar, QMessageBox,
    QFileDialog, QProgressBar, QSplitter, QFrame,
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QAction

from . import __version__
from .api import (
    generate_sudoku,
    solve_sudoku,
    validate_sudoku,
    llm_play_sudoku,
    evaluate_llm,
    list_llm_providers,
    list_available_models,
)
from .core import SudokuGame, PlayMode


class SudokuCell(QLineEdit):
    def __init__(self, row: int, col: int):
        super().__init__()
        self.row = row
        self.col = col
        self.setMaxLength(1)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(40, 40)
        font = QFont("Monaco", 16, QFont.Bold)
        self.setFont(font)
        self._is_fixed = False

    def set_fixed(self, value: int):
        self.setText(str(value) if value != 0 else "")
        self.setReadOnly(value != 0)
        self._is_fixed = value != 0

    def get_value(self) -> int:
        text = self.text().strip()
        return int(text) if text.isdigit() and 1 <= int(text) <= 9 else 0


class SudokuGrid(QWidget):
    def __init__(self):
        super().__init__()
        self.cells = [[SudokuCell(r, c) for c in range(9)] for r in range(9)]
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        for box_row in range(3):
            box_layout = QHBoxLayout()
            for box_col in range(3):
                frame = QFrame()
                frame.setFrameStyle(QFrame.Box | QFrame.Raised)
                frame.setLineWidth(2)
                grid = QGridLayout(frame)
                grid.setSpacing(2)
                
                for r in range(3):
                    for c in range(3):
                        row = box_row * 3 + r
                        col = box_col * 3 + c
                        grid.addWidget(self.cells[row][col], r, c)
                
                box_layout.addWidget(frame)
            layout.addLayout(box_layout)

    def set_puzzle(self, puzzle: list[list[int]]):
        for r in range(9):
            for c in range(9):
                self.cells[r][c].set_fixed(puzzle[r][c])

    def get_grid(self) -> list[list[int]]:
        return [[self.cells[r][c].get_value() for c in range(9)] for r in range(9)]

    def clear(self):
        for r in range(9):
            for c in range(9):
                self.cells[r][c].clear()
                self.cells[r][c].setReadOnly(False)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_game: Optional[SudokuGame] = None
        self._setup_ui()
        self._load_providers()

    def _setup_ui(self):
        self.setWindowTitle(f"SudokuAI v{__version__}")
        self.setMinimumSize(1000, 700)

        self._create_menu_bar()
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        self._create_control_panel(left_layout)
        self._create_llm_panel(left_layout)
        left_layout.addStretch()

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        self._create_sudoku_panel(right_layout)
        self._create_log_panel(right_layout)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([250, 750])
        main_layout.addWidget(splitter)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _create_menu_bar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")
        
        new_action = QAction("&New Game", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_game)
        file_menu.addAction(new_action)

        open_action = QAction("&Open...", self)
        open_action.triggered.connect(self.open_game)
        file_menu.addAction(open_action)

        save_action = QAction("&Save Results...", self)
        save_action.triggered.connect(self.save_results)
        file_menu.addAction(save_action)

        file_menu.addSeparator()
        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        game_menu = menubar.addMenu("&Game")
        
        solve_action = QAction("&Solve", self)
        solve_action.triggered.connect(self.solve_current)
        game_menu.addAction(solve_action)

        validate_action = QAction("&Validate", self)
        validate_action.triggered.connect(self.validate_current)
        game_menu.addAction(validate_action)

        llm_menu = menubar.addMenu("&LLM")
        
        play_action = QAction("&Play Current Game", self)
        play_action.triggered.connect(self.llm_play)
        llm_menu.addAction(play_action)

        evaluate_action = QAction("&Evaluate Model...", self)
        evaluate_action.triggered.connect(self.llm_evaluate)
        llm_menu.addAction(evaluate_action)

        help_menu = menubar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def _create_control_panel(self, parent_layout):
        group = QGroupBox("Game Controls")
        layout = QVBoxLayout(group)

        diff_layout = QHBoxLayout()
        diff_layout.addWidget(QLabel("Difficulty:"))
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["easy", "medium", "hard", "expert", "master"])
        diff_layout.addWidget(self.difficulty_combo)
        layout.addLayout(diff_layout)

        btn_layout = QHBoxLayout()
        self.new_btn = QPushButton("New Game")
        self.new_btn.clicked.connect(self.new_game)
        btn_layout.addWidget(self.new_btn)

        self.solve_btn = QPushButton("Solve")
        self.solve_btn.clicked.connect(self.solve_current)
        btn_layout.addWidget(self.solve_btn)
        layout.addLayout(btn_layout)

        parent_layout.addWidget(group)

    def _create_llm_panel(self, parent_layout):
        group = QGroupBox("LLM Configuration")
        layout = QVBoxLayout(group)

        provider_layout = QHBoxLayout()
        provider_layout.addWidget(QLabel("Provider:"))
        self.provider_combo = QComboBox()
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        provider_layout.addWidget(self.provider_combo)
        layout.addLayout(provider_layout)

        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        model_layout.addWidget(self.model_combo)
        
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedWidth(30)
        refresh_btn.setToolTip("Refresh model list")
        refresh_btn.clicked.connect(self._refresh_models)
        model_layout.addWidget(refresh_btn)
        layout.addLayout(model_layout)

        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["step", "oneshot"])
        mode_layout.addWidget(self.mode_combo)
        layout.addLayout(mode_layout)

        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(self.test_connection)
        layout.addWidget(test_btn)

        self.play_btn = QPushButton("Let LLM Play")
        self.play_btn.clicked.connect(self.llm_play)
        layout.addWidget(self.play_btn)

        self.evaluate_btn = QPushButton("Evaluate Model")
        self.evaluate_btn.clicked.connect(self.llm_evaluate)
        layout.addWidget(self.evaluate_btn)

        parent_layout.addWidget(group)

    def _create_sudoku_panel(self, parent_layout):
        group = QGroupBox("Sudoku Board")
        layout = QVBoxLayout(group)

        self.sudoku_grid = SudokuGrid()
        layout.addWidget(self.sudoku_grid, alignment=Qt.AlignCenter)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        parent_layout.addWidget(group)

    def _create_log_panel(self, parent_layout):
        group = QGroupBox("Evaluation Log")
        layout = QVBoxLayout(group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)

        parent_layout.addWidget(group)

    def _load_providers(self):
        result = list_llm_providers()
        if result.success:
            self.provider_combo.addItems(result.data.keys())
            self._refresh_models()

    def _on_provider_changed(self, provider: str):
        self._refresh_models()

    def _refresh_models(self):
        provider = self.provider_combo.currentText()
        if not provider:
            return
        
        result = list_available_models(provider)
        if result.success:
            models = result.data.get("models", [])
            self.model_combo.clear()
            if models:
                self.model_combo.addItems(models)
                self.log(f"Loaded {len(models)} models for {provider}")
            else:
                self.model_combo.setPlaceholderText("Enter model name")
                self.log(f"No models found for {provider}")
        else:
            self.log(f"Error loading models: {result.error}")

    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def new_game(self):
        difficulty = self.difficulty_combo.currentText()
        result = generate_sudoku(difficulty)
        
        if result.success:
            self.current_game = SudokuGame(
                id=result.data["id"],
                puzzle=result.data["puzzle"],
                solution=result.data["solution"],
                difficulty=result.data["difficulty"],
                clues=result.data["clues"],
            )
            self.sudoku_grid.set_puzzle(self.current_game.puzzle)
            self.log(f"New {difficulty} game generated ({self.current_game.clues} clues)")
            self.status_bar.showMessage(f"Game: {difficulty} | Clues: {self.current_game.clues}")
        else:
            QMessageBox.warning(self, "Error", f"Failed to generate game: {result.error}")

    def solve_current(self):
        if not self.current_game:
            QMessageBox.warning(self, "Warning", "No game loaded. Generate a new game first.")
            return
        
        self.sudoku_grid.set_puzzle(self.current_game.solution)
        self.log("Puzzle solved")

    def validate_current(self):
        grid = self.sudoku_grid.get_grid()
        result = validate_sudoku(grid)
        
        if result.success and result.data["is_valid"]:
            QMessageBox.information(self, "Valid", "Solution is correct!")
            self.log("Solution validated: correct")
        else:
            QMessageBox.warning(self, "Invalid", "Solution is not correct.")
            self.log("Solution validated: incorrect")

    def test_connection(self):
        provider = self.provider_combo.currentText()
        model = self.model_combo.currentText() or "gemma3:4b"
        self.log(f"Testing connection to {provider}/{model}...")
        self.status_bar.showMessage(f"Testing {model}...")

    def llm_play(self):
        if not self.current_game:
            QMessageBox.warning(self, "Warning", "No game loaded. Generate a new game first.")
            return
        
        provider = self.provider_combo.currentText()
        model = self.model_combo.currentText() or "gemma3:4b"
        mode = self.mode_combo.currentText()

        self.log(f"Starting LLM play: {model} ({mode} mode)")
        self.status_bar.showMessage(f"LLM playing...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        result = llm_play_sudoku(
            difficulty=self.current_game.difficulty,
            provider=provider,
            model=model,
            mode=mode,
        )

        self.progress_bar.setVisible(False)

        if result.success:
            data = result.data
            self.log(f"Game completed: {'correct' if data['correct'] else 'incorrect'}")
            self.log(f"Moves: {data['total_moves']} ({data['valid_moves']} valid, {data['invalid_moves']} invalid)")
            self.log(f"Time: {data['time_elapsed']:.1f}s")
            
            if data.get("final_board"):
                self.sudoku_grid.set_puzzle(data["final_board"])
            
            self.status_bar.showMessage(f"Completed: {'Correct' if data['correct'] else 'Incorrect'}")
        else:
            self.log(f"Error: {result.error}")
            self.status_bar.showMessage("Error during play")

    def llm_evaluate(self):
        provider = self.provider_combo.currentText()
        model = self.model_combo.currentText() or "gemma3:4b"
        mode = self.mode_combo.currentText()

        self.log(f"Starting evaluation: {model}")
        self.status_bar.showMessage("Evaluating...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        result = evaluate_llm(
            provider=provider,
            model=model,
            games_per_difficulty=2,
            difficulties=["easy", "medium"],
            mode=mode,
        )

        self.progress_bar.setVisible(False)

        if result.success:
            data = result.data
            self.log(f"Evaluation complete: {data['overall_accuracy']:.1%} accuracy")
            self.log(f"Games: {data['total_games']}, Correct: {data['correct_games']}")
            self.status_bar.showMessage(f"Accuracy: {data['overall_accuracy']:.1%}")
        else:
            self.log(f"Error: {result.error}")
            self.status_bar.showMessage("Evaluation failed")

    def open_game(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open Game", "", "JSON Files (*.json)"
        )
        if filepath:
            import json
            from pathlib import Path
            data = json.loads(Path(filepath).read_text())
            self.current_game = SudokuGame.from_dict(data)
            self.sudoku_grid.set_puzzle(self.current_game.puzzle)
            self.log(f"Loaded game from {filepath}")

    def save_results(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Results", "", "JSON Files (*.json)"
        )
        if filepath and self.current_game:
            from pathlib import Path
            import json
            Path(filepath).write_text(json.dumps(self.current_game.to_dict(), indent=2))
            self.log(f"Saved to {filepath}")

    def show_about(self):
        QMessageBox.about(
            self,
            f"About SudokuAI",
            f"SudokuAI v{__version__}\n\n"
            "A Sudoku game platform for LLM evaluation.\n\n"
            "Features:\n"
            "- Generate puzzles with 5 difficulty levels\n"
            "- LLM integration for autonomous gameplay\n"
            "- Evaluation and benchmarking tools\n"
            "- CLI, GUI, and Web interfaces\n\n"
            "Licensed under GPLv3",
        )


def run_gui():
    app = QApplication(sys.argv)
    app.setApplicationName("SudokuAI")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(run_gui())