"""Batch trainer for Q-Learning on the Assistant (PC/server)."""

from __future__ import annotations

import random
from pathlib import Path
from typing import List
from datetime import datetime, timezone

import numpy as np

from shared.src.config.q_learning_settings import QLearningSettings
from shared.src.models.q_learning_models import Transition
from shared.src.models.rl_core_models import TabularQCheckpointMetadata
from shared.src.utils.logging_factory import get_logger
from shared.src.learning.q_learning.approximators.tabular import TabularQ
from shared.src.learning.q_learning.io.serialization import save_tabular_checkpoint
from assistant.src.learning.q_learning.replay_loader import ReplayLoader

logger = get_logger("q_learning.trainer.assistant")


class AssistantTrainer:
    """Offline/batch trainer for improving the Q-policy on the Assistant."""

    def __init__(
        self,
        config: QLearningSettings,
        experience_dir: Path = Path("data/experience"),
        checkpoint_path: Path = Path("checkpoints/tabular_q_improved.npz"),
    ):
        self.config = config
        self.loader = ReplayLoader(data_dir=experience_dir)
        self.checkpoint_path = checkpoint_path

        # Larger Q-table capacity for training (can be bigger than edge)
        self.q_agent = TabularQ(config=config, replay_capacity=100_000)

        logger.info(
            "Assistant trainer initialized",
            experience_dir=str(experience_dir),
            checkpoint_path=str(checkpoint_path),
        )

    def train_on_dump(self, num_epochs: int = 10, batch_size: int = 64) -> dict:
        """Load latest experience dump and perform batch updates."""
        transitions = self.loader.load_latest_dump()
        if not transitions:
            logger.warning("No transitions available for training")
            return {"trained": False, "num_transitions": 0}

        logger.info("Starting batch training", num_transitions=len(transitions))

        total_td_error = 0.0
        update_count = 0

        for epoch in range(num_epochs):
            random.shuffle(transitions)  # simple shuffle
            for i in range(0, len(transitions), batch_size):
                batch = transitions[i : i + batch_size]

                for t in batch:
                    td_error = self.q_agent.update_from_transition(t)
                    total_td_error += td_error
                    update_count += 1

            logger.debug(
                "Training epoch complete",
                epoch=epoch + 1,
                avg_td_error=total_td_error / update_count if update_count > 0 else 0.0,
            )

        avg_td_error = total_td_error / update_count if update_count > 0 else 0.0

        # Save improved checkpoint
        metadata = TabularQCheckpointMetadata(
            created_at=datetime.now(timezone.utc),
            episode_count=len(transitions),  # approximate
            total_steps=update_count,
            avg_reward_last_100=0.0,  # TODO: compute from loaded data if available
            epsilon=self.config.epsilon_min,  # training usually exploits
            source="central",
            rolling_avg_td_error=avg_td_error,
        )

        success = save_tabular_checkpoint(
            q_table=self.q_agent.q_table,
            metadata=metadata,
            filepath=self.checkpoint_path,
        )

        stats = {
            "trained": success,
            "num_transitions": len(transitions),
            "num_updates": update_count,
            "avg_td_error": avg_td_error,
            "checkpoint_saved": success,
            "checkpoint_path": str(self.checkpoint_path),
        }

        logger.info("Training complete", **stats)
        return stats
