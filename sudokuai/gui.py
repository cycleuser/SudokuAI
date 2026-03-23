"""
Graphical user interface for SudokuAI using PySide6.
Features animated step-by-step gameplay with thought bubbles.
"""

from __future__ import annotations

import sys
import threading
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QLabel, QLineEdit, QComboBox,
    QSpinBox, QGroupBox, QTableWidget, QTableWidgetItem,
    QTabWidget, QTextEdit, QStatusBar, QMenuBar, QMessageBox,
    QFileDialog, QProgressBar, QSplitter, QFrame, QScrollArea,
    QSizePolicy, QGraphicsOpacityEffect, QStyle,
)
from PySide6.QtCore import (
    Qt, QTimer, Signal, QPropertyAnimation, QPoint,
    QEasingCurve, Property, QThread, QMutex, QRect,
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
        self.setStyleSheet("""
            #thoughtBubble {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #E3F2FD, stop:1 #BBDEFB);
                border: 2px solid #1976D2;
                border-radius: 16px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)
        
        self.header = QLabel("🧠 AI Thinking...")
        self.header.setStyleSheet("font-weight: bold; color: #0D47A1; border: none; background: transparent;")
        self.header.setFont(QFont("SF Pro Display", 13, QFont.Bold))
        layout.addWidget(self.header)
        
        self.content = QLabel("Waiting for move...")
        self.content.setWordWrap(True)
        self.content.setStyleSheet("color: #37474F; border: none; background: transparent; line-height: 1.4;")
        self.content.setFont(QFont("SF Pro Display", 11))
        self.content.setMinimumHeight(40)
        self.content.setMaximumHeight(100)
        layout.addWidget(self.content)
        
        self.step_label = QLabel("Step: 0")
        self.step_label.setStyleSheet("color: #78909C; font-size: 11px; border: none; background: transparent;")
        layout.addWidget(self.step_label)
        
        self.setMinimumWidth(300)
        self.setMaximumWidth(400)

    def set_thought(self, text: str, step: int = 0, is_valid: bool = True):
        self._current_text = text
        self.content.setText(text)
        self.step_label.setText(f"Step: {step}")
        
        if is_valid:
            self.setStyleSheet("""
                #thoughtBubble {
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #E8F5E9, stop:1 #C8E6C9);
                    border: 2px solid #388E3C;
                    border-radius: 16px;
                }
            """)
            self.header.setText("✅ Valid Move")
            self.header.setStyleSheet("font-weight: bold; color: #1B5E20; border: none; background: transparent;")
        else:
            self.setStyleSheet("""
                #thoughtBubble {
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #FFEBEE, stop:1 #FFCDD2);
                    border: 2px solid #D32F2F;
                    border-radius: 16px;
                }
            """)
            self.header.setText("❌ Invalid Move")
            self.header.setStyleSheet("font-weight: bold; color: #B71C1C; border: none; background: transparent;")

    def set_thinking(self):
        self.setStyleSheet("""
            #thoughtBubble {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFF8E1, stop:1 #FFECB3);
                border: 2px solid #FFA000;
                border-radius: 16px;
            }
        """)
        self.header.setText("🧠 Thinking...")
        self.header.setStyleSheet("font-weight: bold; color: #FF6F00; border: none; background: transparent;")
        self.content.setText("Analyzing the board...")

    def set_error(self, error_msg: str, step: int = 0):
        self._current_text = error_msg
        self.content.setText(error_msg)
        self.step_label.setText(f"Step: {step}")
        self.setStyleSheet("""
            #thoughtBubble {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFEBEE, stop:1 #FFCDD2);
                border: 3px solid #D32F2F;
                border-radius: 16px;
            }
        """)
        self.header.setText("⚠️ Error / Parse Failed")
        self.header.setStyleSheet("font-weight: bold; color: #B71C1C; border: none; background: transparent;")

    def animate_shake(self):
        pass


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
        self.setObjectName("toastWidget")
        self.setStyleSheet("""
            #toastWidget {
                background-color: rgba(38, 50, 56, 230);
                border-radius: 8px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)
        
        self.icon_label = QLabel("⚠️")
        self.icon_label.setStyleSheet("font-size: 18px; border: none; background: transparent;")
        layout.addWidget(self.icon_label)
        
        self.message_label = QLabel("Error message")
        self.message_label.setStyleSheet("color: white; font-size: 13px; border: none; background: transparent;")
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)
        
        self.setFixedHeight(50)
        self.setMinimumWidth(200)
        self.setMaximumWidth(400)

    def show_error(self, message: str, duration: int = 3000):
        self.icon_label.setText("❌")
        self.message_label.setText(message)
        self.setStyleSheet("""
            #toastWidget {
                background-color: rgba(183, 28, 28, 230);
                border-radius: 8px;
            }
        """)
        self._show_toast(duration)

    def show_warning(self, message: str, duration: int = 3000):
        self.icon_label.setText("⚠️")
        self.message_label.setText(message)
        self.setStyleSheet("""
            #toastWidget {
                background-color: rgba(230, 81, 0, 230);
                border-radius: 8px;
            }
        """)
        self._show_toast(duration)

    def show_success(self, message: str, duration: int = 2000):
        self.icon_label.setText("✅")
        self.message_label.setText(message)
        self.setStyleSheet("""
            #toastWidget {
                background-color: rgba(27, 94, 32, 230);
                border-radius: 8px;
            }
        """)
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
        self.setFixedSize(52, 52)
        self._is_fixed = False
        self._opacity = 1.0
        self._highlight_color = None
        self._original_style = ""
        self._apply_base_style()

    def _apply_base_style(self):
        self.setStyleSheet("""
            QLineEdit {
                background-color: white;
                color: #1A237E;
                border: 1px solid #B0BEC5;
                font-size: 22px;
                font-weight: bold;
                selection-background-color: #E3F2FD;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
                background-color: #FAFAFA;
            }
        """)

    def set_fixed(self, value: int):
        self.setText(str(value) if value != 0 else "")
        self.setReadOnly(value != 0)
        self._is_fixed = value != 0
        if value != 0:
            self.setStyleSheet("""
                QLineEdit {
                    background-color: #ECEFF1;
                    color: #263238;
                    border: 1px solid #B0BEC5;
                    font-size: 22px;
                    font-weight: bold;
                }
            """)
        else:
            self._apply_base_style()
        self._original_style = self.styleSheet()

    def get_value(self) -> int:
        text = self.text().strip()
        return int(text) if text.isdigit() and 1 <= int(text) <= 9 else 0

    def highlight_animated(self, color: str = "#4CAF50", duration: int = 400):
        self._highlight_color = color
        bg_color = "#C8E6C9" if color == "#4CAF50" else "#E3F2FD"
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {bg_color};
                color: {color};
                border: 2px solid {color};
                font-size: 22px;
                font-weight: bold;
            }}
        """)
        QTimer.singleShot(duration, self._fade_to_normal)

    def highlight_error(self, duration: int = 800):
        self.setStyleSheet("""
            QLineEdit {
                background-color: #FFCDD2;
                color: #C62828;
                border: 3px solid #E53935;
                font-size: 22px;
                font-weight: bold;
            }
        """)
        self._shake_animation()
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
            self.setStyleSheet("""
                QLineEdit {
                    background-color: #E3F2FD;
                    color: #1565C0;
                    border: 1px solid #64B5F6;
                    font-size: 22px;
                    font-weight: bold;
                }
            """)
            QTimer.singleShot(300, self._apply_base_style)
        else:
            self.setStyleSheet(self._original_style)

    def set_value_animated(self, value: int, is_valid: bool = True, reasoning: str = ""):
        self.setText(str(value))
        if is_valid:
            self.highlight_animated("#43A047", 500)
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
        self.board_widget.setFixedSize(480, 480)
        self.board_widget.setStyleSheet("""
            QWidget {
                background-color: white;
            }
        """)
        
        main_layout = QVBoxLayout(self.board_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        for box_row in range(3):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(0)
            
            for box_col in range(3):
                box_widget = QWidget()
                box_widget.setStyleSheet(self._get_box_style(box_row, box_col))
                box_layout = QGridLayout(box_widget)
                box_layout.setContentsMargins(1, 1, 1, 1)
                box_layout.setSpacing(0)
                
                for r in range(3):
                    for c in range(3):
                        row = box_row * 3 + r
                        col = box_col * 3 + c
                        cell = self.cells[row][col]
                        box_layout.addWidget(cell, r, c)
                        cell.textChanged.connect(
                            lambda text, cr=row, cc=col: self._on_cell_changed(cr, cc, text)
                        )
                
                row_layout.addWidget(box_widget)
            
            main_layout.addWidget(row_widget)
        
        layout.addWidget(self.board_widget, alignment=Qt.AlignCenter)

    def _get_box_style(self, box_row: int, box_col: int) -> str:
        is_center = (box_row == 1) or (box_col == 1)
        return """
            QWidget {
                border: 2px solid #37474F;
                background-color: white;
            }
        """

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
        cell.set_value_animated(value, is_valid, reasoning)
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
            self.cells[r][c].setStyleSheet("""
                QLineEdit {
                    background-color: #FFEB3B;
                    color: #C62828;
                    border: 2px solid #FF5722;
                    font-size: 22px;
                    font-weight: bold;
                }
            """)
        
        if conflicting_cells:
            QTimer.singleShot(800, lambda: self._clear_conflict_highlights(conflicting_cells))

    def _clear_conflict_highlights(self, cells):
        for r, c in cells:
            cell = self.cells[r][c]
            if not cell._is_fixed:
                cell._apply_base_style()
            else:
                cell.setStyleSheet(cell._original_style)

    def shake_board(self):
        original_pos = self.board_widget.pos()
        shake_steps = [
            QPoint(original_pos.x() - 6, original_pos.y()),
            QPoint(original_pos.x() + 6, original_pos.y()),
            QPoint(original_pos.x() - 4, original_pos.y()),
            QPoint(original_pos.x() + 4, original_pos.y()),
            QPoint(original_pos.x() - 2, original_pos.y()),
            QPoint(original_pos.x() + 2, original_pos.y()),
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
                            row_vals = [self.board.get(row, c) for c in range(9) if self.board.get(row, c) != 0]
                            col_vals = [self.board.get(r, col) for r in range(9) if self.board.get(r, col) != 0]
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
        self.layout.setSpacing(12)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setStyleSheet("""
            QScrollArea { 
                border: none; 
                background: transparent; 
            }
            QScrollBar:vertical {
                border: none;
                background: #F5F5F5;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #BDBDBD;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.setContentsMargins(5, 5, 8, 5)
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
        self._setup_ui()
        self._load_providers()

    def _setup_ui(self):
        self.setWindowTitle(f"SudokuAI v{__version__}")
        self.setMinimumSize(1250, 800)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FAFAFA;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #E0E0E0;
                border-radius: 10px;
                margin-top: 12px;
                padding-top: 12px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
                color: #37474F;
            }
            QPushButton {
                padding: 10px 20px;
                border-radius: 8px;
                background-color: #2196F3;
                color: white;
                border: none;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QPushButton:disabled {
                background-color: #CFD8DC;
                color: #90A4AE;
            }
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #CFD8DC;
                border-radius: 6px;
                background: white;
                font-size: 12px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
            QSpinBox {
                padding: 6px 10px;
                border: 1px solid #CFD8DC;
                border-radius: 6px;
                background: white;
            }
            QLabel {
                color: #37474F;
            }
        """)

        self._create_menu_bar()
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        left_panel = QWidget()
        left_panel.setMaximumWidth(300)
        left_panel.setMinimumWidth(260)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(15)

        self._create_control_panel(left_layout)
        self._create_llm_panel(left_layout)
        self._create_playback_panel(left_layout)
        left_layout.addStretch()

        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setSpacing(20)
        center_layout.setContentsMargins(0, 0, 0, 0)
        self._create_sudoku_panel(center_layout)

        right_panel = QWidget()
        right_panel.setMaximumWidth(380)
        right_panel.setMinimumWidth(320)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(15)
        self._create_thought_panel(right_layout)
        self._create_log_panel(right_layout)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(center_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 500, 380])
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("QSplitter::handle { background: #E0E0E0; }")
        main_layout.addWidget(splitter)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #263238;
                color: #ECEFF1;
                font-size: 12px;
                padding: 4px 10px;
            }
        """)
        self.status_bar.showMessage("Ready - Generate a new game to start")
        
        self.toast = ToastWidget(self)

    def _create_menu_bar(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #37474F;
                color: white;
                padding: 4px 8px;
            }
            QMenuBar::item:selected {
                background-color: #546E7A;
            }
            QMenu {
                background-color: white;
                border: 1px solid #E0E0E0;
            }
            QMenu::item:selected {
                background-color: #E3F2FD;
            }
        """)

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

        help_menu = menubar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def _create_control_panel(self, parent_layout):
        group = QGroupBox("🎮 Game Controls")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)

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
        self.solve_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        self.solve_btn.clicked.connect(self.solve_current)
        btn_layout.addWidget(self.solve_btn)
        layout.addLayout(btn_layout)

        parent_layout.addWidget(group)

    def _create_llm_panel(self, parent_layout):
        group = QGroupBox("🤖 LLM Configuration")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)

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
        refresh_btn.setFixedWidth(40)
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

        test_btn = QPushButton("🔌 Test Connection")
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
            }
            QPushButton:hover {
                background-color: #546E7A;
            }
        """)
        test_btn.clicked.connect(self.test_connection)
        layout.addWidget(test_btn)

        parent_layout.addWidget(group)

    def _create_playback_panel(self, parent_layout):
        group = QGroupBox("⏯ Playback Controls")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)

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
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        self.play_btn.clicked.connect(self.llm_play)
        btn_layout.addWidget(self.play_btn)

        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.pause_btn.setEnabled(False)
        btn_layout.addWidget(self.pause_btn)
        layout.addLayout(btn_layout)

        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_play)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #E0E0E0;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)

        parent_layout.addWidget(group)

    def _create_sudoku_panel(self, parent_layout):
        group = QGroupBox("🧩 Sudoku Board")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)

        self.sudoku_grid = SudokuGridWidget()
        layout.addWidget(self.sudoku_grid, alignment=Qt.AlignCenter)

        parent_layout.addWidget(group)

    def _create_thought_panel(self, parent_layout):
        group = QGroupBox("💭 AI Thoughts")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 12, 12, 12)

        self.thought_container = ThoughtBubbleContainer()
        layout.addWidget(self.thought_container)

        parent_layout.addWidget(group)

    def _create_log_panel(self, parent_layout):
        group = QGroupBox("📋 Activity Log")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 12, 12, 12)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(140)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #263238;
                color: #B0BEC5;
                border: none;
                border-radius: 6px;
                font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
                font-size: 11px;
                padding: 8px;
            }
        """)
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
                self.model_combo.setPlaceholderText("Enter model name")
                self.log(f"⚠ No models found for {provider}")
        else:
            self.log(f"✗ Error loading models: {result.error}")

    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"<span style='color: #78909C;'>[{timestamp}]</span> {message}")

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
        model = self.model_combo.currentText() or "gemma3:4b"
        mode = self.mode_combo.currentText()

        if mode == "oneshot":
            self._play_oneshot(provider, model)
        else:
            self._play_step_by_step(provider, model)

    def _play_step_by_step(self, provider: str, model: str):
        from .core import DEFAULT_PROVIDERS
        
        config = DEFAULT_PROVIDERS.get(provider)
        if not config:
            self.log(f"✗ Unknown provider: {provider}")
            return
        
        if model:
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
            self.log(f"  <span style='color: #4CAF50;'>✓</span> Step {move.step}: ({move.row},{move.col})={move.value}")
        else:
            self.log(f"  <span style='color: #F44336;'>✗</span> Step {move.step}: ({move.row},{move.col})={move.value} - <span style='color: #FF5722;'>{move.error_detail}</span>")
            self.sudoku_grid.shake_board()
            self.toast.show_error(f"Invalid: {move.error_detail[:40]}...", 2500)

    def _on_parse_error(self, error_msg: str, step: int):
        self.thought_container.add_error(error_msg, step)
        self.log(f"  <span style='color: #FF9800;'>⚠️</span> Step {step}: Parse error - {error_msg[:80]}...")
        self.toast.show_warning(f"Parse error at step {step}", 2500)

    def _on_error(self, error: str, step: int):
        self.thought_container.add_error(error, step)
        self.log(f"  <span style='color: #F44336;'>✗</span> Step {step}: Error - {error}")
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
        model = self.model_combo.currentText() or "gemma3:4b"
        mode = self.mode_combo.currentText()

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
            f"<li>CLI, GUI, and Web interfaces</li>"
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
    
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(250, 250, 250))
    palette.setColor(QPalette.WindowText, QColor(55, 71, 79))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ToolTipText, QColor(55, 71, 79))
    palette.setColor(QPalette.Text, QColor(55, 71, 79))
    palette.setColor(QPalette.Button, QColor(255, 255, 255))
    palette.setColor(QPalette.ButtonText, QColor(55, 71, 79))
    palette.setColor(QPalette.Highlight, QColor(33, 150, 243))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)
    
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(run_gui())