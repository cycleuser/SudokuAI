"""
Prompt templates for LLM Sudoku gameplay.
"""

import re
from typing import Optional, Tuple, List


def format_board_for_prompt(grid: List[List[int]]) -> str:
    lines = []
    for i, row in enumerate(grid):
        if i % 3 == 0 and i != 0:
            lines.append("  ------+-------+------")
        line_parts = []
        for j, val in enumerate(row):
            if j % 3 == 0 and j != 0:
                line_parts.append("|")
            line_parts.append(str(val) if val != 0 else ".")
        lines.append("  " + " ".join(line_parts))
    return "\n".join(lines)


def build_step_prompt(grid: List[List[int]], step: int, previous_moves: List[dict] = None) -> str:
    board_str = format_board_for_prompt(grid)
    
    prompt = f"""You are playing a Sudoku puzzle. Fill in ONE cell at a time.

Current board (step {step}):
{board_str}

Rules:
- Each row must contain digits 1-9 without repetition
- Each column must contain digits 1-9 without repetition  
- Each 3x3 box must contain digits 1-9 without repetition

Respond in this exact format:
THINKING: <brief reasoning why this number goes here>
MOVE: <row>,<col>,<value>

Example response:
THINKING: In row 0, the only missing number is 7
MOVE: 0,2,7

Now make your move:"""
    
    return prompt


def build_oneshot_prompt(grid: List[List[int]]) -> str:
    board_str = format_board_for_prompt(grid)
    
    prompt = f"""Solve this Sudoku puzzle. Provide the complete solution.

Puzzle:
{board_str}

Rules:
- Each row must contain digits 1-9 without repetition
- Each column must contain digits 1-9 without repetition
- Each 3x3 box must contain digits 1-9 without repetition

Provide your solution as a 9x9 grid of numbers. Format:

SOLUTION:
<row 1 as 9 digits>
<row 2 as 9 digits>
...
<row 9 as 9 digits>

Example:
SOLUTION:
534678912
672195348
198342567
...

Now provide the complete solution:"""
    
    return prompt


def parse_move(response: str) -> Optional[Tuple[int, int, int, str]]:
    move_pattern = r"MOVE:\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)"
    match = re.search(move_pattern, response, re.IGNORECASE)
    
    if match:
        row = int(match.group(1))
        col = int(match.group(2))
        value = int(match.group(3))
        
        thinking_pattern = r"THINKING:\s*(.+?)(?=MOVE:|$)"
        thinking_match = re.search(thinking_pattern, response, re.IGNORECASE | re.DOTALL)
        reasoning = thinking_match.group(1).strip() if thinking_match else ""
        
        return row, col, value, reasoning
    
    return None


def parse_solution(response: str) -> Optional[List[List[int]]]:
    solution_pattern = r"SOLUTION:\s*\n([\d\s\n]+)"
    match = re.search(solution_pattern, response, re.IGNORECASE)
    
    if not match:
        lines = [line.strip() for line in response.strip().split("\n") if line.strip()]
        digit_lines = [line for line in lines if len(line) == 9 and line.isdigit()]
        if digit_lines and len(digit_lines) == 9:
            return [[int(c) for c in line] for line in digit_lines]
        return None
    
    solution_text = match.group(1).strip()
    lines = [line.strip() for line in solution_text.split("\n") if line.strip()]
    
    grid = []
    for line in lines:
        clean_line = "".join(c for c in line if c.isdigit())
        if len(clean_line) == 9:
            grid.append([int(c) for c in clean_line])
    
    if len(grid) == 9:
        return grid
    
    return None