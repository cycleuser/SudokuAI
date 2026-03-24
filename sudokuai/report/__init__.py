"""
Report generation module for SudokuAI.
"""

from .generator import generate_evaluation_report, generate_comparison_report
from .templates import REPORT_TEMPLATE, DIFFICULTY_ROW_TEMPLATE

__all__ = [
    "generate_evaluation_report",
    "generate_comparison_report",
    "REPORT_TEMPLATE",
    "DIFFICULTY_ROW_TEMPLATE",
]
