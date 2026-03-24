"""
Game recorder for logging LLM gameplay sessions.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..core import GameMove, PlayResult


class GameRecorder:
    """Records and persists LLM gameplay sessions."""

    def __init__(self, output_dir: str = "logs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.moves: List[GameMove] = []

    def clear(self) -> None:
        self.moves = []

    def log_move(
        self,
        game_id: str,
        step: int,
        row: int,
        col: int,
        value: int,
        is_valid: bool,
        reasoning: str = "",
    ) -> GameMove:
        move = GameMove(
            game_id=game_id,
            step=step,
            row=row,
            col=col,
            value=value,
            is_valid=is_valid,
            reasoning=reasoning,
            timestamp=datetime.now(),
        )
        self.moves.append(move)
        return move

    def save_play_result(
        self, result: PlayResult, filename: Optional[str] = None
    ) -> Path:
        if filename is None:
            filename = f"play_{result.game_id}_{result.model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        filepath = self.output_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

        return filepath

    def export_log(self, filename: str = "game_log.json") -> Path:
        filepath = self.output_dir / filename
        data = {
            "exported_at": datetime.now().isoformat(),
            "total_moves": len(self.moves),
            "moves": [m.to_dict() for m in self.moves],
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return filepath

    def get_summary(self) -> dict:
        if not self.moves:
            return {"total": 0, "valid": 0, "invalid": 0, "valid_rate": 0.0}

        valid = sum(1 for m in self.moves if m.is_valid)
        total = len(self.moves)
        return {
            "total": total,
            "valid": valid,
            "invalid": total - valid,
            "valid_rate": valid / total if total > 0 else 0.0,
        }
