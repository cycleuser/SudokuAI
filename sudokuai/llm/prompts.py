"""
Prompt templates for LLM Sudoku gameplay.
Includes comprehensive education module for teaching Sudoku rules and strategies.
"""

import re
from typing import Optional, Tuple, List, Set


SUDOKU_EDUCATION = """
## SUDOKU GAME EDUCATION MODULE

You are an expert Sudoku solver. This guide teaches you the rules and strategies.

### BASIC RULES

1. **Grid Structure**: A Sudoku puzzle is a 9×9 grid divided into nine 3×3 boxes.
   
2. **Three Constraints**:
   - Each ROW must contain digits 1-9 exactly once
   - Each COLUMN must contain digits 1-9 exactly once  
   - Each 3×3 BOX must contain digits 1-9 exactly once

3. **Coordinate System**: 
   - Rows are numbered 0-8 (top to bottom)
   - Columns are numbered 0-8 (left to right)
   - Cell (row, col) means the cell at that position

### SOLVING STRATEGIES (USE IN ORDER)

**Strategy 1: SINGLE CANDIDATE (Easiest)**
Find a cell where only ONE number can possibly go.
- Check what numbers are already in the row
- Check what numbers are already in the column
- Check what numbers are already in the 3×3 box
- If only one number is missing, that's your answer!

**Strategy 2: SINGLE POSITION**
Find a row/column/box where a specific number can only go in ONE place.
- In a row: if 5 is missing and can only go in one empty cell, place it there
- Same logic for columns and boxes

**Strategy 3: ELIMINATION**
When you can't find a single candidate:
- For each empty cell, list ALL possible values
- Look for cells with fewest possibilities (2-3 candidates)
- Make educated guesses and verify

### STEP-BY-STEP PROCESS

For each move, follow this EXACT process:

1. **SCAN**: Look at the entire board
2. **IDENTIFY**: Find the easiest cell to fill (fewest candidates)
3. **VERIFY**: Double-check your choice against all three constraints
4. **EXECUTE**: Place your number

### EXAMPLE WALKTHROUGH

Given this partial board:
```
5 3 . | . 7 . | . . .
6 . . | 1 9 5 | . . .
. 9 8 | . . . | . 6 .
------+-------+------
```

Cell (0,2) - Let's find what can go here:
- Row 0 already has: 5, 3, 7
- Column 2 already has: 8
- Box 0 (top-left 3×3) has: 5, 3, 6, 9, 8
- Missing from row 0: 1, 2, 4, 6, 8, 9
- But checking constraints: can't be 6, 8, 9 (in column or box)
- Possible: 1, 2, 4
- Need more information - let's look elsewhere

Cell (1,1) - What can go here?
- Row 1 has: 6, 1, 9, 5
- Column 1 has: 3, 9
- Box 0 has: 5, 3, 6, 9, 8
- Missing: 2, 4, 7
- Only possibilities: 2, 4, 7
- Still need more info...

Cell (2,0) - Let's check:
- Row 2 has: 9, 8, 6
- Column 0 has: 5, 6
- Box 0 has: 5, 3, 6, 9, 8
- Possible values: 1, 2, 4, 7

### COMMON MISTAKES TO AVOID

1. **Placing a duplicate number**: Always verify the number isn't already in row/column/box
2. **Wrong coordinates**: Remember (row, col) not (col, row)
3. **Guessing too early**: Always try elimination first
4. **Not checking all constraints**: Must check row AND column AND box

### OUTPUT FORMAT

Always respond in this EXACT format:
```
THINKING: <your step-by-step reasoning>
MOVE: <row>,<col>,<value>
```

Your THINKING should explain:
- What cell you're targeting and why
- What numbers are already present (row/col/box)
- What number you choose and why

Example good response:
```
THINKING: Looking at cell (0,2). Row 0 has 5,3,7. Column 2 has 8. Box has 5,3,6,9,8. 
Eliminating: 5,3,7,8,6,9. Candidates: 1,2,4. Checking row 0 again... 
Actually, let me find a better cell. Cell (1,1) - Row 1: 6,1,9,5. Col 1: 3,9. Box: 5,3,6,9,8.
Wait, cell (2,3) looks promising. Row 2: 9,8,6. Column 3: 1. Box 1: 1,9,5,7.
I'll place 4 at (0,2) as it's the safest move given current information.
MOVE: 0,2,4
```

---

Now you understand Sudoku. Let's play!
"""


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


def get_possible_values(grid: List[List[int]], row: int, col: int) -> Set[int]:
    if grid[row][col] != 0:
        return set()
    
    used = set()
    
    for c in range(9):
        if grid[row][c] != 0:
            used.add(grid[row][c])
    
    for r in range(9):
        if grid[r][col] != 0:
            used.add(grid[r][col])
    
    box_row, box_col = 3 * (row // 3), 3 * (col // 3)
    for r in range(box_row, box_row + 3):
        for c in range(box_col, box_col + 3):
            if grid[r][c] != 0:
                used.add(grid[r][c])
    
    return set(range(1, 10)) - used


def find_best_cell(grid: List[List[int]]) -> Tuple[int, int, Set[int]]:
    best_cell = None
    min_candidates = 10
    
    for r in range(9):
        for c in range(9):
            if grid[r][c] == 0:
                candidates = get_possible_values(grid, r, c)
                if len(candidates) < min_candidates:
                    min_candidates = len(candidates)
                    best_cell = (r, c, candidates)
                    if min_candidates == 1:
                        return best_cell
    
    return best_cell if best_cell else (0, 0, set())


def format_hints_for_cell(grid: List[List[int]], row: int, col: int) -> str:
    possible = get_possible_values(grid, row, col)
    
    row_vals = [grid[row][c] for c in range(9) if grid[row][c] != 0]
    col_vals = [grid[r][col] for r in range(9) if grid[r][col] != 0]
    
    box_row, box_col = 3 * (row // 3), 3 * (col // 3)
    box_vals = []
    for r in range(box_row, box_row + 3):
        for c in range(box_col, box_col + 3):
            if grid[r][c] != 0:
                box_vals.append(grid[r][c])
    
    return f"""Cell ({row},{col}) analysis:
  - Row {row} contains: {sorted(row_vals) if row_vals else 'empty'}
  - Column {col} contains: {sorted(col_vals) if col_vals else 'empty'}
  - Box contains: {sorted(box_vals) if box_vals else 'empty'}
  - Possible values: {sorted(possible) if possible else 'none (filled)'}"""


def build_educational_intro() -> str:
    return SUDOKU_EDUCATION


def build_step_prompt(grid: List[List[int]], step: int, previous_moves: List = None, 
                      last_error: str = None, last_move: dict = None, 
                      is_first_move: bool = False) -> str:
    board_str = format_board_for_prompt(grid)
    
    best_row, best_col, best_candidates = find_best_cell(grid)
    hints = format_hints_for_cell(grid, best_row, best_col)
    
    education_section = ""
    if is_first_move:
        education_section = f"""
{SUDOKU_EDUCATION}

"""
    
    error_feedback = ""
    if last_error and last_move:
        error_feedback = f"""
⚠️ CORRECTION NEEDED - Your last move was INVALID:
You tried: row={last_move.get('row', '?')}, col={last_move.get('col', '?')}, value={last_move.get('value', '?')}
Error: {last_error}

Please analyze this error. What constraint did you violate?
- Did you place a number that already exists in the ROW?
- Did you place a number that already exists in the COLUMN?
- Did you place a number that already exists in the 3×3 BOX?

Make a different, VALID move.

"""
    
    move_history = ""
    if previous_moves and len(previous_moves) > 0:
        recent = previous_moves[-5:] if len(previous_moves) > 5 else previous_moves
        move_history = "\nYour recent moves:\n"
        for m in recent:
            status = "✓ CORRECT" if m.is_valid else "✗ WRONG"
            move_history += f"  {status}: ({m.row},{m.col})={m.value}"
            if m.reasoning:
                move_history += f" - {m.reasoning[:40]}"
            if not m.is_valid and m.error_detail:
                move_history += f" [Error: {m.error_detail[:30]}]"
            move_history += "\n"
        move_history += "\n"
    
    empty_count = sum(1 for r in range(9) for c in range(9) if grid[r][c] == 0)
    
    prompt = f"""{education_section}=== CURRENT GAME STATE ===

Step: {step}
Empty cells remaining: {empty_count}

Current board:
{board_str}

{move_history}{error_feedback}=== HELPFUL ANALYSIS ===

I found a cell with good possibilities:
{hints}

You can use this information, or analyze any other cell yourself.

=== YOUR TASK ===

Make ONE valid move. Follow this process:

1. CHOOSE a cell (I suggest ({best_row},{best_col}) with possibilities {sorted(best_candidates) if best_candidates else 'analyze yourself'})
2. VERIFY the number isn't in the same row, column, or 3×3 box
3. RESPOND in this EXACT format:

THINKING: <explain your analysis - what numbers are in row/col/box, why you chose this value>
MOVE: <row>,<col>,<value>

Example correct format:
THINKING: Cell (2,4). Row 2 has 3,7,1. Column 4 has 5,9. Box has 3,5,7,9. Missing: 2,4,6,8. I'll try 4.
MOVE: 2,4,4

Now make your move:"""
    
    return prompt


def build_error_feedback_prompt(grid: List[List[int]], step: int, error_detail: str,
                                failed_move: dict, possible_values: set = None) -> str:
    board_str = format_board_for_prompt(grid)
    
    analysis = format_hints_for_cell(grid, failed_move['row'], failed_move['col'])
    
    hint = ""
    if possible_values:
        hint = f"\n✅ Valid values for cell ({failed_move['row']},{failed_move['col']}): {sorted(possible_values)}"
    
    alternative_cells = ""
    best_row, best_col, best_candidates = find_best_cell(grid)
    if best_candidates:
        alternative_cells = f"""

💡 SUGGESTION: Try cell ({best_row},{best_col}) instead.
{format_hints_for_cell(grid, best_row, best_col)}"""
    
    prompt = f"""❌ MOVE REJECTED

Your move ({failed_move['row']},{failed_move['col']})={failed_move['value']} was INVALID!

Reason: {error_detail}{hint}{alternative_cells}

=== CURRENT BOARD ===
{board_str}

=== WHAT WENT WRONG? ===

Let's understand the Sudoku rules again:
- Each number 1-9 can appear ONLY ONCE per row
- Each number 1-9 can appear ONLY ONCE per column  
- Each number 1-9 can appear ONLY ONCE per 3×3 box

Your chosen value {failed_move['value']} already exists somewhere in the same row, column, or box.

=== TRY AGAIN ===

Choose a DIFFERENT cell or a DIFFERENT value.
Double-check by asking yourself:
1. Is this cell empty?
2. Does this row already have this number?
3. Does this column already have this number?
4. Does this 3×3 box already have this number?

Respond in this format:
THINKING: <your corrected reasoning>
MOVE: <row>,<col>,<value>

Your corrected move:"""
    
    return prompt


def build_oneshot_prompt(grid: List[List[int]]) -> str:
    board_str = format_board_for_prompt(grid)
    empty_count = sum(1 for r in range(9) for c in range(9) if grid[r][c] == 0)
    
    prompt = f"""{SUDOKU_EDUCATION}

=== PUZZLE TO SOLVE ===

Solve this Sudoku puzzle completely. {empty_count} cells need to be filled.

Puzzle:
{board_str}

=== INSTRUCTIONS ===

Solve the entire puzzle using Sudoku rules:
- Each row: 1-9 exactly once
- Each column: 1-9 exactly once
- Each 3×3 box: 1-9 exactly once

Provide your solution as a 9x9 grid:

SOLUTION:
<row 0 as 9 digits>
<row 1 as 9 digits>
...
<row 8 as 9 digits>

Example format:
SOLUTION:
534678912
672195348
198342567
...

Your complete solution:"""
    
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