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


def build_step_prompt(grid: List[List[int]], step: int, previous_moves: List = None, 
                      last_error: str = None, last_move: dict = None) -> str:
    board_str = format_board_for_prompt(grid)
    
    error_feedback = ""
    if last_error and last_move:
        error_feedback = f"""
⚠️ FEEDBACK - YOUR LAST MOVE WAS INVALID:
You tried: row={last_move.get('row', '?')}, col={last_move.get('col', '?')}, value={last_move.get('value', '?')}
Error: {last_error}
Please analyze this error and make a CORRECT move now.

"""
    
    move_history = ""
    if previous_moves and len(previous_moves) > 0:
        recent_moves = previous_moves[-3:] if len(previous_moves) > 3 else previous_moves
        move_history = "\nRecent moves:\n"
        for m in recent_moves:
            status = "✓" if m.is_valid else "✗"
            move_history += f"  {status} ({m.row},{m.col})={m.value}: {m.reasoning[:50] if m.reasoning else 'no reasoning'}\n"
        move_history += "\n"
    
    prompt = f"""You are playing a Sudoku puzzle. Fill in ONE cell at a time.
{error_feedback}
Current board (step {step}):
{board_str}
{move_history}
Rules:
- Each row must contain digits 1-9 without repetition
- Each column must contain digits 1-9 without repetition  
- Each 3x3 box must contain digits 1-9 without repetition

IMPORTANT: 
- Analyze the board carefully before making a move
- Check that your chosen number doesn't already exist in the same row, column, or 3x3 box
- If you made an error before, learn from it and avoid the same mistake

Respond in this exact format:
THINKING: <brief reasoning why this number goes here>
MOVE: <row>,<col>,<value>

Example response:
THINKING: In row 0, the only missing number is 7
MOVE: 0,2,7

Now make your move:"""
    
    return prompt


def build_error_feedback_prompt(grid: List[List[int]], step: int, error_detail: str,
                                failed_move: dict, possible_values: set = None) -> str:
    board_str = format_board_for_prompt(grid)
    
    possible_hint = ""
    if possible_values:
        possible_hint = f"\n💡 Hint: Valid values for cell ({failed_move['row']},{failed_move['col']}) are: {sorted(possible_values)}"
    
    prompt = f"""❌ ERROR - Your previous move was INVALID!

You attempted to place {failed_move['value']} at position ({failed_move['row']},{failed_move['col']}).

Error details: {error_detail}{possible_hint}

Current board state:
{board_str}

Please make a DIFFERENT, VALID move. Double-check:
1. The cell is empty (contains 0 or .)
2. The value is not already in the same row
3. The value is not already in the same column  
4. The value is not already in the same 3x3 box

Respond in this exact format:
THINKING: <corrected reasoning for a valid move>
MOVE: <row>,<col>,<value>

Your corrected move:"""
    
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