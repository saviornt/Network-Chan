"""Replay loader for the Assistant – aggregates experience from edge."""

from __future__ import annotations

from pathlib import Path
from typing import List

from shared.src.models.q_learning_models import Transition
from shared.src.utils.logging_factory import get_logger

logger = get_logger("q_learning.trainer.replay_loader")


class ReplayLoader:
    """Loads transitions from edge-generated files or MQTT dumps."""

    def __init__(self, data_dir: Path = Path("data/experience")):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def load_from_json_file(self, filepath: Path) -> List[Transition]:
        """Load transitions from a single JSON file (one transition per line)."""
        transitions: List[Transition] = []

        if not filepath.exists():
            logger.warning("Replay file not found", path=str(filepath))
            return transitions

        try:
            with filepath.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        t = Transition.model_validate_json(line)
                        transitions.append(t)
                    except Exception as e:
                        logger.error(
                            "Invalid transition JSON line – skipping",
                            error=str(e),
                            line_preview=line[:100],
                        )
            logger.info(
                "Loaded transitions from file",
                path=str(filepath),
                count=len(transitions),
            )
        except Exception as e:
            logger.exception(
                "Failed to load replay file",
                path=str(filepath),
                error=str(e),
            )

        return transitions

    def load_latest_dump(self) -> List[Transition]:
        """Load from the most recent JSON dump in data_dir."""
        files = sorted(self.data_dir.glob("experience_dump_*.json"), reverse=True)
        if not files:
            logger.info("No experience dumps found")
            return []

        latest = files[0]
        return self.load_from_json_file(latest)
