"""
Graphical user interface for SudokuAI using PySide6.
Features animated step-by-step gameplay with thought bubbles.
"""

from __future__ import annotations

import sys
import json
import threading
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QLabel, QLineEdit, QComboBox,
    QSpinBox, QGroupBox, QTableWidget, QTableWidgetItem,
    QTabWidget, QTextEdit, QStatusBar, QMenuBar, QMessageBox,
    QFileDialog, QProgressBar, QSplitter, QFrame, QScrollArea,
    QSizePolicy, QGraphicsOpacityEffect, QStyle, QCheckBox,
)
from PySide6.QtCore import (
    Qt, QTimer, Signal, QPropertyAnimation, QPoint,
    QEasingCurve, Property, QThread, QMutex, QRect, QSettings,
)
from PySide6.QtGui import QFont, QAction, QColor, QPalette, QPainter, QBrush, QPen, QFontDatabase

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
from .core import SudokuGame, PlayMode, LLMConfig, GameMove
from .sudoku.board import SudokuBoard
from .sudoku.validator import SudokuValidator
from .llm.client import LLMClient
from .llm.prompts import build_step_prompt, parse_move, build_error_feedback_prompt


@dataclass
class AnimatedMove:
    row: int
    col: int
    value: int
    is_valid: bool
    reasoning: str
    step: int
    error_detail: str = ""


class ThoughtBubble(QFrame):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._current_text = ""

    def _setup_ui(self):
        self.setObjectName("thoughtBubble")
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(1)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        
        self.header = QLabel("🧠 AI Thinking...")
        self.header.setFont(QFont("", 12, QFont.Bold))
        layout.addWidget(self.header)
        
        self.content = QLabel("Waiting for move...")
        self.content.setWordWrap(True)
        self.content.setFont(QFont("", 11))
        self.content.setMinimumHeight(40)
        self.content.setMaximumHeight(100)
        layout.addWidget(self.content)
        
        self.step_label = QLabel("Step: 0")
        self.step_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(self.step_label)
        
        self.setMinimumWidth(280)
        self.setMaximumWidth(400)

    def set_thought(self, text: str, step: int = 0, is_valid: bool = True):
        self._current_text = text
        self.content.setText(text)
        self.step_label.setText(f"Step: {step}")
        
        if is_valid:
            self.header.setText("✅ Valid Move")
            self.header.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.header.setText("❌ Invalid Move")
            self.header.setStyleSheet("color: red; font-weight: bold;")

    def set_thinking(self):
        self.header.setText("🧠 Thinking...")
        self.header.setStyleSheet("color: orange; font-weight: bold;")
        self.content.setText("Analyzing the board...")

    def set_error(self, error_msg: str, step: int = 0):
        self._current_text = error_msg
        self.content.setText(error_msg)
        self.step_label.setText(f"Step: {step}")
        self.header.setText("⚠️ Error")
        self.header.setStyleSheet("color: red; font-weight: bold;")


class ToastWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._hide_timer = QTimer()
        self._hide_timer.timeout.connect(self.hide_toast)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(8)
        
        self.icon_label = QLabel("⚠️")
        self.icon_label.setFont(QFont("", 16))
        layout.addWidget(self.icon_label)
        
        self.message_label = QLabel("Error message")
        self.message_label.setStyleSheet("color: white; font-size: 13px;")
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)
        
        self.setFixedHeight(45)
        self.setMinimumWidth(200)
        self.setMaximumWidth(400)

    def show_error(self, message: str, duration: int = 3000):
        self.icon_label.setText("❌")
        self.message_label.setText(message)
        self.setStyleSheet("background-color: rgba(183, 28, 28, 230); border-radius: 8px;")
        self._show_toast(duration)

    def show_warning(self, message: str, duration: int = 3000):
        self.icon_label.setText("⚠️")
        self.message_label.setText(message)
        self.setStyleSheet("background-color: rgba(230, 81, 0, 230); border-radius: 8px;")
        self._show_toast(duration)

    def show_success(self, message: str, duration: int = 2000):
        self.icon_label.setText("✅")
        self.message_label.setText(message)
        self.setStyleSheet("background-color: rgba(27, 94, 32, 230); border-radius: 8px;")
        self._show_toast(duration)

    def _show_toast(self, duration: int):
        if self.parent():
            parent_rect = self.parent().rect()
            x = (parent_rect.width() - self.width()) // 2
            y = 20
            self.move(x, y)
        
        self.show()
        self._opacity_animation(0, 1, 200)
        self._hide_timer.start(duration)

    def hide_toast(self):
        self._hide_timer.stop()
        self._opacity_animation(1, 0, 200)
        QTimer.singleShot(200, self.hide)

    def _opacity_animation(self, start: int, end: int, duration: int):
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(start)
        animation.setEndValue(end)
        animation.start()
        self._animation = animation


class SudokuCell(QLineEdit):
    def __init__(self, row: int, col: int):
        super().__init__()
        self.row = row
        self.col = col
        self.setMaxLength(1)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(50, 50)
        self._is_fixed = False
        self._original_style = ""
        font = QFont("", 20, QFont.Bold)
        self.setFont(font)

    def set_fixed(self, value: int):
        self.setText(str(value) if value != 0 else "")
        self.setReadOnly(value != 0)
        self._is_fixed = value != 0
        if value != 0:
            self.setStyleSheet("background-color: palette(window); font-weight: bold;")
        self._original_style = self.styleSheet()

    def get_value(self) -> int:
        text = self.text().strip()
        return int(text) if text.isdigit() and 1 <= int(text) <= 9 else 0

    def highlight_valid(self, duration: int = 500):
        self.setStyleSheet("background-color: #C8E6C9; color: #2E7D32; font-weight: bold; border: 2px solid #43A047;")
        QTimer.singleShot(duration, self._fade_to_normal)

    def highlight_error(self, duration: int = 800):
        self.setStyleSheet("background-color: #FFCDD2; color: #C62828; font-weight: bold; border: 2px solid #E53935;")
        self._shake_animation()
        QTimer.singleShot(duration, self._fade_to_normal)

    def highlight_conflict(self, duration: int = 600):
        self.setStyleSheet("background-color: #FFF9C4; color: #F57F17; font-weight: bold; border: 2px solid #FFB300;")
        QTimer.singleShot(duration, self._fade_to_normal)

    def _shake_animation(self):
        original_pos = self.pos()
        shake_steps = [
            QPoint(original_pos.x() - 4, original_pos.y()),
            QPoint(original_pos.x() + 4, original_pos.y()),
            QPoint(original_pos.x() - 3, original_pos.y()),
            QPoint(original_pos.x() + 3, original_pos.y()),
            QPoint(original_pos.x() - 2, original_pos.y()),
            QPoint(original_pos.x() + 2, original_pos.y()),
            original_pos,
        ]
        for i, pos in enumerate(shake_steps):
            QTimer.singleShot(i * 50, lambda p=pos: self.move(p))

    def _fade_to_normal(self):
        if not self._is_fixed:
            self.setStyleSheet("background-color: #E3F2FD; color: #1565C0; font-weight: bold;")
            QTimer.singleShot(300, lambda: self.setStyleSheet(""))
        else:
            self.setStyleSheet(self._original_style)

    def set_value_animated(self, value: int, is_valid: bool = True):
        self.setText(str(value))
        if is_valid:
            self.highlight_valid(500)
        else:
            self.highlight_error(800)


class SudokuGridWidget(QWidget):
    cell_clicked = Signal(int, int)
    
    def __init__(self):
        super().__init__()
        self.cells = [[SudokuCell(r, c) for c in range(9)] for r in range(9)]
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.board_widget = QWidget()
        self.board_widget.setFixedSize(460, 460)
        
        main_layout = QVBoxLayout(self.board_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        for box_row in range(3):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(0)
            
            for box_col in range(3):
                box_frame = QFrame()
                box_frame.setFrameStyle(QFrame.Box | QFrame.Plain)
                box_frame.setLineWidth(2)
                
                box_grid = QGridLayout(box_frame)
                box_grid.setContentsMargins(1, 1, 1, 1)
                box_grid.setSpacing(0)
                
                for r in range(3):
                    for c in range(3):
                        row = box_row * 3 + r
                        col = box_col * 3 + c
                        cell = self.cells[row][col]
                        box_grid.addWidget(cell, r, c)
                        cell.textChanged.connect(
                            lambda text, cr=row, cc=col: self._on_cell_changed(cr, cc, text)
                        )
                
                row_layout.addWidget(box_frame)
            
            main_layout.addWidget(row_widget)
        
        layout.addWidget(self.board_widget, alignment=Qt.AlignCenter)

    def _on_cell_changed(self, row: int, col: int, text: str):
        self.cell_clicked.emit(row, col)

    def set_puzzle(self, puzzle: list[list[int]]):
        for r in range(9):
            for c in range(9):
                self.cells[r][c].set_fixed(puzzle[r][c])

    def get_grid(self) -> list[list[int]]:
        return [[self.cells[r][c].get_value() for c in range(9)] for r in range(9)]

    def set_cell_animated(self, row: int, col: int, value: int, is_valid: bool = True, reasoning: str = ""):
        cell = self.cells[row][col]
        cell.set_value_animated(value, is_valid)
        if not is_valid:
            self._highlight_conflicts(row, col, value)

    def _highlight_conflicts(self, row: int, col: int, value: int):
        conflicting_cells = []
        for c in range(9):
            if c != col and self.cells[row][c].get_value() == value:
                conflicting_cells.append((row, c))
        for r in range(9):
            if r != row and self.cells[r][col].get_value() == value:
                conflicting_cells.append((r, col))
        box_row, box_col = 3 * (row // 3), 3 * (col // 3)
        for r in range(box_row, box_row + 3):
            for c in range(box_col, box_col + 3):
                if (r, c) != (row, col) and self.cells[r][c].get_value() == value:
                    if (r, c) not in conflicting_cells:
                        conflicting_cells.append((r, c))
        
        for r, c in conflicting_cells:
            self.cells[r][c].highlight_conflict(800)

    def shake_board(self):
        original_pos = self.board_widget.pos()
        shake_steps = [
            QPoint(original_pos.x() - 5, original_pos.y()),
            QPoint(original_pos.x() + 5, original_pos.y()),
            QPoint(original_pos.x() - 3, original_pos.y()),
            QPoint(original_pos.x() + 3, original_pos.y()),
            original_pos,
        ]
        for i, pos in enumerate(shake_steps):
            QTimer.singleShot(i * 60, lambda p=pos: self.board_widget.move(p))

    def clear(self):
        for r in range(9):
            for c in range(9):
                self.cells[r][c].clear()
                self.cells[r][c].setReadOnly(False)

    def clear_user_input(self):
        for r in range(9):
            for c in range(9):
                if not self.cells[r][c]._is_fixed:
                    self.cells[r][c].clear()


class StepPlayWorker(QThread):
    move_ready = Signal(object)
    play_finished = Signal(bool, int, int)
    error_occurred = Signal(str, int)
    progress_update = Signal(int, int)
    parse_error = Signal(str, int)
    
    def __init__(self, game: SudokuGame, client: LLMClient, speed_ms: int = 1000):
        super().__init__()
        self.game = game
        self.client = client
        self.speed_ms = speed_ms
        self._paused = False
        self._stopped = False
        self._mutex = QMutex()
        self.moves: List[AnimatedMove] = []
        self.board = SudokuBoard(game.puzzle)
        self.solution = SudokuBoard(game.solution)
        self.step = 0
        self.last_error = None
        self.last_failed_move = None

    def run(self):
        from .llm.prompts import build_error_feedback_prompt
        max_moves = 500
        empty_count = len(self.board.get_empty_cells())
        
        while self.step < max_moves and not self._stopped:
            self._mutex.lock()
            if self._paused:
                self._mutex.unlock()
                self.msleep(100)
                continue
            self._mutex.unlock()
            
            empty_cells = self.board.get_empty_cells()
            if not empty_cells:
                break
            
            current_empty = len(empty_cells)
            self.progress_update.emit(empty_count - current_empty, empty_count)
            
            if self.last_error and self.last_failed_move:
                possible = self.board.get_possible_values(self.last_failed_move['row'], self.last_failed_move['col'])
                prompt = build_error_feedback_prompt(
                    self.board.grid, self.step + 1, self.last_error,
                    self.last_failed_move, possible
                )
            else:
                prompt = build_step_prompt(self.board.grid, self.step + 1, self.moves,
                                          self.last_error, self.last_failed_move)
            
            try:
                response = self.client.chat(prompt)
                parsed = parse_move(response.content)
                
                if not parsed:
                    error_msg = f"Could not parse response. LLM said: \"{response.content[:150]}...\""
                    self.parse_error.emit(error_msg, self.step + 1)
                    move = AnimatedMove(
                        row=0, col=0, value=0,
                        is_valid=False, reasoning="Parse failed - invalid response format",
                        step=self.step + 1, error_detail=error_msg
                    )
                    self.moves.append(move)
                    self.last_error = error_msg
                    self.last_failed_move = {'row': 0, 'col': 0, 'value': 0}
                    self.step += 1
                    self.msleep(self.speed_ms)
                    continue
                
                row, col, value, reasoning = parsed
                
                if not (0 <= row < 9 and 0 <= col < 9 and 1 <= value <= 9):
                    error_msg = f"Out of bounds: ({row},{col})={value}. Row/col must be 0-8, value 1-9."
                    self.parse_error.emit(error_msg, self.step + 1)
                    safe_row = max(0, min(8, row))
                    safe_col = max(0, min(8, col))
                    safe_value = max(1, min(9, value))
                    move = AnimatedMove(
                        row=safe_row, col=safe_col, value=safe_value,
                        is_valid=False, reasoning=reasoning,
                        step=self.step + 1, error_detail=error_msg
                    )
                    self.moves.append(move)
                    self.last_error = error_msg
                    self.last_failed_move = {'row': safe_row, 'col': safe_col, 'value': safe_value}
                    self.step += 1
                    self.msleep(self.speed_ms)
                    continue
                
                is_valid = SudokuValidator.is_valid_move(self.board, row, col, value)
                
                error_detail = ""
                if not is_valid:
                    current_val = self.board.get(row, col)
                    if current_val != 0:
                        error_detail = f"Cell ({row},{col}) already filled with {current_val}!"
                    else:
                        possible = self.board.get_possible_values(row, col)
                        if value not in possible:
                            error_detail = f"Conflict! {value} exists in row/col/box. Valid options: {sorted(possible)}"
                        else:
                            error_detail = "Invalid move (unknown reason)"
                    
                    self.last_error = error_detail
                    self.last_failed_move = {'row': row, 'col': col, 'value': value}
                else:
                    self.last_error = None
                    self.last_failed_move = None
                
                move = AnimatedMove(
                    row=row, col=col, value=value,
                    is_valid=is_valid, reasoning=reasoning,
                    step=self.step + 1, error_detail=error_detail
                )
                self.moves.append(move)
                
                self.move_ready.emit(move)
                
                if is_valid:
                    self.board.set(row, col, value)
                
                self.msleep(self.speed_ms)
                self.step += 1
                
            except Exception as e:
                error_msg = f"Exception: {str(e)}"
                self.error_occurred.emit(error_msg, self.step + 1)
                self.last_error = error_msg
                self.step += 1
        
        is_correct = self.board == self.solution
        self.play_finished.emit(is_correct, len(self.moves), sum(1 for m in self.moves if m.is_valid))

    def pause(self):
        self._mutex.lock()
        self._paused = True
        self._mutex.unlock()

    def resume(self):
        self._mutex.lock()
        self._paused = False
        self._mutex.unlock()

    def stop(self):
        self._stopped = True

    def set_speed(self, ms: int):
        self.speed_ms = ms


class ThoughtBubbleContainer(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._bubbles: List[ThoughtBubble] = []
        self._max_bubbles = 5

    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(8)
        self.scroll_layout.setContentsMargins(5, 5, 5, 5)
        self.scroll_layout.addStretch()
        
        self.scroll.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll)

    def add_thought(self, text: str, step: int, is_valid: bool = True, error_detail: str = ""):
        while len(self._bubbles) >= self._max_bubbles:
            old_bubble = self._bubbles.pop(0)
            self.scroll_layout.removeWidget(old_bubble)
            old_bubble.deleteLater()
        
        bubble = ThoughtBubble()
        if error_detail:
            full_text = f"{text}\n\n⚠️ {error_detail}"
            bubble.set_thought(full_text, step, is_valid)
        else:
            bubble.set_thought(text, step, is_valid)
        self._bubbles.append(bubble)
        
        self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, bubble)
        
        QTimer.singleShot(50, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))

    def add_error(self, error_msg: str, step: int):
        while len(self._bubbles) >= self._max_bubbles:
            old_bubble = self._bubbles.pop(0)
            self.scroll_layout.removeWidget(old_bubble)
            old_bubble.deleteLater()
        
        bubble = ThoughtBubble()
        bubble.set_error(error_msg, step)
        self._bubbles.append(bubble)
        
        self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, bubble)
        
        QTimer.singleShot(50, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))

    def set_thinking(self):
        if self._bubbles:
            self._bubbles[-1].set_thinking()
        else:
            bubble = ThoughtBubble()
            bubble.set_thinking()
            self._bubbles.append(bubble)
            self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, bubble)

    def clear(self):
        for bubble in self._bubbles:
            self.scroll_layout.removeWidget(bubble)
            bubble.deleteLater()
        self._bubbles.clear()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_game: Optional[SudokuGame] = None
        self._play_worker: Optional[StepPlayWorker] = None
        self._is_playing = False
        self._speed_ms = 1000
        self._is_dark_mode = False
        self._settings = QSettings("SudokuAI", "SudokuAI")
        self._load_theme_preference()
        self._setup_ui()
        self._load_providers()
        self._apply_initial_theme()

    def _load_theme_preference(self):
        self._is_dark_mode = self._settings.value("dark_mode", False, type=bool)

    def _save_theme_preference(self):
        self._settings.setValue("dark_mode", self._is_dark_mode)

    def _apply_initial_theme(self):
        if self._is_dark_mode:
            self._apply_dark_mode()

    def toggle_theme(self):
        self._is_dark_mode = not self._is_dark_mode
        self._save_theme_preference()
        
        if self._is_dark_mode:
            self._apply_dark_mode()
        else:
            self._apply_light_mode()
        
        self.theme_checkbox.setChecked(self._is_dark_mode)
        self.dark_theme_action.setChecked(self._is_dark_mode)

    def _apply_dark_mode(self):
        app = QApplication.instance()
        app.setStyle("Fusion")
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.Base, QColor(35, 35, 35))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, QColor(25, 25, 25))
        palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
        app.setPalette(palette)

    def _apply_light_mode(self):
        app = QApplication.instance()
        app.setStyle("Fusion")
        app.setPalette(QPalette())

    def _setup_ui(self):
        self.setWindowTitle(f"SudokuAI v{__version__}")
        self.setMinimumSize(1150, 750)

        self._create_menu_bar()
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        left_panel = QWidget()
        left_panel.setMaximumWidth(280)
        left_panel.setMinimumWidth(240)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(12)

        self._create_control_panel(left_layout)
        self._create_llm_panel(left_layout)
        self._create_playback_panel(left_layout)
        left_layout.addStretch()

        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setSpacing(15)
        center_layout.setContentsMargins(0, 0, 0, 0)
        self._create_sudoku_panel(center_layout)

        right_panel = QWidget()
        right_panel.setMaximumWidth(340)
        right_panel.setMinimumWidth(280)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(12)
        self._create_thought_panel(right_layout)
        self._create_log_panel(right_layout)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(center_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([280, 480, 340])
        main_layout.addWidget(splitter)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Generate a new game to start")
        
        self.toast = ToastWidget(self)

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
        play_action.setShortcut("Ctrl+P")
        play_action.triggered.connect(self.llm_play)
        llm_menu.addAction(play_action)

        evaluate_action = QAction("&Evaluate Model...", self)
        evaluate_action.triggered.connect(self.llm_evaluate)
        llm_menu.addAction(evaluate_action)

        view_menu = menubar.addMenu("&View")
        
        self.dark_theme_action = QAction("🌙 Dark Mode", self, checkable=True)
        self.dark_theme_action.setChecked(self._is_dark_mode)
        self.dark_theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(self.dark_theme_action)

        help_menu = menubar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def _create_control_panel(self, parent_layout):
        group = QGroupBox("Game Controls")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)

        diff_layout = QHBoxLayout()
        diff_layout.addWidget(QLabel("Difficulty:"))
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["easy", "medium", "hard", "expert", "master"])
        diff_layout.addWidget(self.difficulty_combo)
        layout.addLayout(diff_layout)

        btn_layout = QHBoxLayout()
        self.new_btn = QPushButton("🎲 New Game")
        self.new_btn.clicked.connect(self.new_game)
        btn_layout.addWidget(self.new_btn)

        self.solve_btn = QPushButton("💡 Solve")
        self.solve_btn.clicked.connect(self.solve_current)
        btn_layout.addWidget(self.solve_btn)
        layout.addLayout(btn_layout)
        
        theme_layout = QHBoxLayout()
        self.theme_checkbox = QCheckBox("🌙 Dark Mode")
        self.theme_checkbox.setChecked(self._is_dark_mode)
        self.theme_checkbox.stateChanged.connect(lambda: self.toggle_theme() if self.theme_checkbox.isChecked() != self._is_dark_mode else None)
        theme_layout.addWidget(self.theme_checkbox)
        theme_layout.addStretch()
        layout.addLayout(theme_layout)

        parent_layout.addWidget(group)

    def _create_llm_panel(self, parent_layout):
        group = QGroupBox("LLM Configuration")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)

        provider_layout = QHBoxLayout()
        provider_layout.addWidget(QLabel("Provider:"))
        self.provider_combo = QComboBox()
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        provider_layout.addWidget(self.provider_combo)
        layout.addLayout(provider_layout)

        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        model_layout.addWidget(self.model_combo)
        
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedWidth(35)
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

        self.test_btn = QPushButton("🔌 Test Connection")
        self.test_btn.clicked.connect(self.test_connection)
        layout.addWidget(self.test_btn)

        parent_layout.addWidget(group)

    def _create_playback_panel(self, parent_layout):
        group = QGroupBox("Playback Controls")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)

        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Speed:"))
        self.speed_slider = QSpinBox()
        self.speed_slider.setRange(100, 3000)
        self.speed_slider.setValue(1000)
        self.speed_slider.setSingleStep(100)
        self.speed_slider.setSuffix(" ms")
        self.speed_slider.valueChanged.connect(self._on_speed_changed)
        speed_layout.addWidget(self.speed_slider)
        layout.addLayout(speed_layout)

        btn_layout = QHBoxLayout()
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.clicked.connect(self.llm_play)
        btn_layout.addWidget(self.play_btn)

        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.pause_btn.setEnabled(False)
        btn_layout.addWidget(self.pause_btn)
        layout.addLayout(btn_layout)

        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.clicked.connect(self.stop_play)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        parent_layout.addWidget(group)

    def _create_sudoku_panel(self, parent_layout):
        group = QGroupBox("Sudoku Board")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.sudoku_grid = SudokuGridWidget()
        layout.addWidget(self.sudoku_grid, alignment=Qt.AlignCenter)

        parent_layout.addWidget(group)

    def _create_thought_panel(self, parent_layout):
        group = QGroupBox("AI Thoughts")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(10, 10, 10, 10)

        self.thought_container = ThoughtBubbleContainer()
        layout.addWidget(self.thought_container)

        parent_layout.addWidget(group)

    def _create_log_panel(self, parent_layout):
        group = QGroupBox("Activity Log")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(10, 10, 10, 10)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(130)
        layout.addWidget(self.log_text)

        parent_layout.addWidget(group)

    def _load_providers(self):
        result = list_llm_providers()
        if result.success:
            self.provider_combo.addItems(result.data.keys())
            self._refresh_models()

    def _on_provider_changed(self, provider: str):
        self._refresh_models()

    def _on_speed_changed(self, value: int):
        self._speed_ms = value
        if self._play_worker:
            self._play_worker.set_speed(value)

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
                self.log(f"✓ Loaded {len(models)} models for {provider}")
            else:
                self.model_combo.addItem("No models available")
                self.log(f"⚠ No models found for {provider}")
        else:
            self.log(f"✗ Error loading models: {result.error}")

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
            self.thought_container.clear()
            self.log(f"🎲 New {difficulty} game ({self.current_game.clues} clues)")
            self.status_bar.showMessage(f"Game: {difficulty} | Clues: {self.current_game.clues}")
        else:
            QMessageBox.warning(self, "Error", f"Failed to generate game: {result.error}")

    def solve_current(self):
        if not self.current_game:
            QMessageBox.warning(self, "Warning", "No game loaded. Generate a new game first.")
            return
        
        self.sudoku_grid.set_puzzle(self.current_game.solution)
        self.log("💡 Puzzle solved")

    def validate_current(self):
        grid = self.sudoku_grid.get_grid()
        result = validate_sudoku(grid)
        
        if result.success and result.data["is_valid"]:
            QMessageBox.information(self, "Valid", "Solution is correct!")
            self.log("✅ Solution validated: correct")
        else:
            QMessageBox.warning(self, "Invalid", "Solution is not correct.")
            self.log("❌ Solution validated: incorrect")

    def test_connection(self):
        provider = self.provider_combo.currentText()
        model = self.model_combo.currentText() or "gemma3:4b"
        self.log(f"🔌 Testing connection to {provider}/{model}...")
        self.status_bar.showMessage(f"Testing {model}...")

    def llm_play(self):
        if self._is_playing:
            return
            
        if not self.current_game:
            QMessageBox.warning(self, "Warning", "No game loaded. Generate a new game first.")
            return
        
        provider = self.provider_combo.currentText()
        model = self.model_combo.currentText()
        mode = self.mode_combo.currentText()

        if mode == "oneshot":
            self._play_oneshot(provider, model)
        else:
            self._play_step_by_step(provider, model)

    def _play_step_by_step(self, provider: str, model: str):
        from .core import DEFAULT_PROVIDERS
        
        if not model:
            QMessageBox.warning(self, "Warning", "Please select a model first.")
            return
        
        config = DEFAULT_PROVIDERS.get(provider)
        if not config:
            self.log(f"✗ Unknown provider: {provider}")
            return
        
        config = LLMConfig(
            name=config.name,
            provider=config.provider,
            api_base=config.api_base,
            model=model,
            api_key=config.api_key,
        )
        
        self._is_playing = True
        self._update_play_buttons(True)
        self.sudoku_grid.clear_user_input()
        self.thought_container.clear()
        self.thought_container.set_thinking()
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        self.log(f"▶ Starting step-by-step play: {model}")
        self.status_bar.showMessage(f"LLM playing with {model}...")

        self._play_worker = StepPlayWorker(self.current_game, LLMClient(config), self._speed_ms)
        self._play_worker.move_ready.connect(self._on_move_ready)
        self._play_worker.play_finished.connect(self._on_play_finished)
        self._play_worker.error_occurred.connect(self._on_error)
        self._play_worker.parse_error.connect(self._on_parse_error)
        self._play_worker.progress_update.connect(self._on_progress)
        self._play_worker.start()

    def _play_oneshot(self, provider: str, model: str):
        if not model:
            QMessageBox.warning(self, "Warning", "Please select a model first.")
            return
        
        self.log(f"▶ Starting one-shot play: {model}")
        self.status_bar.showMessage("LLM thinking...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        result = llm_play_sudoku(
            difficulty=self.current_game.difficulty,
            provider=provider,
            model=model,
            mode="oneshot",
        )

        self.progress_bar.setVisible(False)

        if result.success:
            data = result.data
            self.log(f"{'✅' if data['correct'] else '❌'} Game completed: {'correct' if data['correct'] else 'incorrect'}")
            
            if data.get("final_board"):
                self.sudoku_grid.set_puzzle(data["final_board"])
            
            self.status_bar.showMessage(f"Completed: {'Correct' if data['correct'] else 'Incorrect'}")
        else:
            self.log(f"✗ Error: {result.error}")
            self.status_bar.showMessage("Error during play")

    def _on_move_ready(self, move: AnimatedMove):
        if move.value == 0:
            return
        
        self.sudoku_grid.set_cell_animated(move.row, move.col, move.value, move.is_valid, move.reasoning)
        self.thought_container.add_thought(
            move.reasoning or f"Placed {move.value} at ({move.row}, {move.col})", 
            move.step, 
            move.is_valid,
            move.error_detail
        )
        
        if move.is_valid:
            self.log(f"  ✓ Step {move.step}: ({move.row},{move.col})={move.value}")
        else:
            self.log(f"  ✗ Step {move.step}: ({move.row},{move.col})={move.value} - {move.error_detail}")
            self.sudoku_grid.shake_board()
            self.toast.show_error(f"Invalid: {move.error_detail[:40]}...", 2500)

    def _on_parse_error(self, error_msg: str, step: int):
        self.thought_container.add_error(error_msg, step)
        self.log(f"  ⚠️ Step {step}: Parse error - {error_msg[:60]}...")
        self.toast.show_warning(f"Parse error at step {step}", 2500)

    def _on_error(self, error: str, step: int):
        self.thought_container.add_error(error, step)
        self.log(f"  ✗ Step {step}: Error - {error}")
        self.toast.show_error(f"Error: {error[:40]}...", 3000)

    def _on_play_finished(self, is_correct: bool, total_moves: int, valid_moves: int):
        self._is_playing = False
        self._update_play_buttons(False)
        self.progress_bar.setVisible(False)
        
        self.log(f"{'✅' if is_correct else '❌'} Game finished: {'Correct!' if is_correct else 'Incorrect'}")
        self.log(f"  📊 Total: {total_moves} moves, Valid: {valid_moves}")
        
        if is_correct:
            self.toast.show_success(f"Puzzle solved! {valid_moves} valid moves", 4000)
            self.status_bar.showMessage(f"✅ Correct! - {valid_moves}/{total_moves} valid moves")
        else:
            accuracy = valid_moves / total_moves * 100 if total_moves > 0 else 0
            self.toast.show_error(f"Incomplete. Accuracy: {accuracy:.0f}%", 4000)
            self.status_bar.showMessage(f"❌ Incorrect - {valid_moves}/{total_moves} valid moves ({accuracy:.0f}%)")

    def _on_progress(self, filled: int, total: int):
        if total > 0:
            percent = int((filled / total) * 100)
            self.progress_bar.setValue(percent)

    def toggle_pause(self):
        if self._play_worker:
            if self._play_worker._paused:
                self._play_worker.resume()
                self.pause_btn.setText("⏸ Pause")
                self.log("⏯ Playback resumed")
            else:
                self._play_worker.pause()
                self.pause_btn.setText("▶ Resume")
                self.log("⏸ Playback paused")

    def stop_play(self):
        if self._play_worker:
            self._play_worker.stop()
            self._play_worker.wait(2000)
            self._play_worker = None
        
        self._is_playing = False
        self._update_play_buttons(False)
        self.progress_bar.setVisible(False)
        self.log("⏹ Playback stopped")
        self.status_bar.showMessage("Stopped")

    def _update_play_buttons(self, is_playing: bool):
        self.play_btn.setEnabled(not is_playing)
        self.pause_btn.setEnabled(is_playing)
        self.stop_btn.setEnabled(is_playing)
        
        if not is_playing:
            self.pause_btn.setText("⏸ Pause")

    def llm_evaluate(self):
        provider = self.provider_combo.currentText()
        model = self.model_combo.currentText()
        mode = self.mode_combo.currentText()
        
        if not model:
            QMessageBox.warning(self, "Warning", "Please select a model first.")
            return

        self.log(f"📊 Starting evaluation: {model}")
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
            self.log(f"📊 Evaluation complete: {data['overall_accuracy']:.1%} accuracy")
            self.log(f"  Games: {data['total_games']}, Correct: {data['correct_games']}")
            self.status_bar.showMessage(f"Accuracy: {data['overall_accuracy']:.1%}")
        else:
            self.log(f"✗ Error: {result.error}")
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
            self.log(f"📂 Loaded game from {filepath}")

    def save_results(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Results", "", "JSON Files (*.json)"
        )
        if filepath and self.current_game:
            from pathlib import Path
            import json
            Path(filepath).write_text(json.dumps(self.current_game.to_dict(), indent=2))
            self.log(f"💾 Saved to {filepath}")

    def show_about(self):
        QMessageBox.about(
            self,
            f"About SudokuAI",
            f"<h2>SudokuAI v{__version__}</h2>"
            f"<p>A Sudoku game platform for LLM evaluation.</p>"
            f"<p><b>Features:</b></p>"
            f"<ul>"
            f"<li>Animated step-by-step AI gameplay</li>"
            f"<li>Thought bubbles showing AI reasoning</li>"
            f"<li>5 difficulty levels</li>"
            f"<li>Playback controls (pause, resume, speed)</li>"
            f"<li>Light/Dark theme support</li>"
            f"</ul>"
            f"<p>Licensed under <b>GPLv3</b></p>",
        )

    def closeEvent(self, event):
        if self._play_worker:
            self._play_worker.stop()
            self._play_worker.wait(2000)
        event.accept()


def run_gui():
    app = QApplication(sys.argv)
    app.setApplicationName("SudokuAI")
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(run_gui())