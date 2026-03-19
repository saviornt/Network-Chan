"""Q-Learning agent for the Network-Chan Appliance (Raspberry Pi edge).

This is the main runnable agent that:
- Uses TabularQ + replay buffer
- Interacts with environment (dummy for MVP)
- Tracks rolling averages using NumPy
- Exposes rolling avg TD error via Prometheus gauge
- Saves checkpoints with metadata
- Logs everything via the structured logging factory
"""

from __future__ import annotations

from datetime import datetime, timezone
from collections import deque
from pathlib import Path
from typing import Deque, Optional, Literal

import numpy as np
from prometheus_client import Gauge

from shared.src.settings.q_learning_settings import QLearningSettings
from shared.src.models.q_learning_models import Transition
from shared.src.models.rl_core_models import (
    TabularQCheckpointMetadata,
    CheckpointSource,
)
from shared.src.utils.logging_factory import get_logger
from shared.src.learning.q_learning.approximators.tabular import TabularQ
from shared.src.learning.q_learning.io.serialization import save_tabular_checkpoint

from appliance.src.learning.q_learning.dummy_env import DummyNetworkEnv
from appliance.src.settings.agent_settings import AgentSettings
from appliance.src.models.agent_models import AgentEpisodeStats

logger = get_logger("q_learning.agent.appliance")

# Prometheus gauge for observability (exposed on /metrics)
rolling_avg_td_error_gauge = Gauge(
    "qlearn_rolling_avg_td_error",
    "Rolling average TD error over the last N episodes (lower = better convergence)",
)


class ApplianceQLAgent:
    """Production-ready Q-Learning agent for the Appliance edge."""

    def __init__(
        self,
        qlearn_config: Optional[QLearningSettings] = None,
        agent_config: Optional[AgentSettings] = None,
        env: Optional[DummyNetworkEnv] = None,
    ):
        self.qlearn_config = qlearn_config or QLearningSettings()
        self.agent_config = agent_config or AgentSettings()

        self.q_agent = TabularQ(
            config=self.qlearn_config,
            replay_capacity=10_000,
        )
        self.env = env or DummyNetworkEnv()
        self.checkpoint_path = Path(self.agent_config.checkpoint_path)

        # Rolling windows (NumPy for fast mean)
        self.rolling_window = self.agent_config.rolling_window
        self.td_errors_per_episode: Deque[float] = deque(maxlen=self.rolling_window)
        self.rewards_per_episode: Deque[float] = deque(maxlen=self.rolling_window)

        self.episode_count: int = 0
        self.total_steps: int = 0

        logger.info(
            "Appliance Q-Learning agent initialized",
            rolling_window=self.rolling_window,
            checkpoint_interval=self.agent_config.checkpoint_interval,
            initial_epsilon=self.qlearn_config.epsilon_current,
        )

    def run_episode(self, max_steps: Optional[int] = None) -> AgentEpisodeStats:
        """Run one full episode and return rich stats (including rolling averages)."""
        state = self.env.reset()
        total_reward = 0.0
        episode_steps = 0
        done = False
        td_errors: list[float] = []

        logger.info("Episode started", episode=self.episode_count + 1)

        while not done:
            action = self.q_agent.select_action(state=state)
            next_state, reward, done = self.env.step(action)

            transition = Transition(
                state=state,
                action=action,
                reward=reward,
                next_state=next_state,
                done=done,
            )

            td_error = self.q_agent.update_from_transition(transition)
            td_errors.append(td_error)

            total_reward += reward
            episode_steps += 1
            state = next_state

            if max_steps and episode_steps >= max_steps:
                done = True

        self.episode_count += 1
        self.total_steps += episode_steps

        avg_reward = total_reward / episode_steps if episode_steps > 0 else 0.0
        mean_td_error = sum(td_errors) / len(td_errors) if td_errors else 0.0
        max_abs_td_error = max(abs(e) for e in td_errors) if td_errors else 0.0

        # Update rolling windows
        self.td_errors_per_episode.append(mean_td_error)
        self.rewards_per_episode.append(avg_reward)

        # NumPy rolling averages
        rolling_avg_td_error = (
            float(np.mean(self.td_errors_per_episode))
            if self.td_errors_per_episode
            else 0.0
        )
        rolling_avg_reward = (
            float(np.mean(self.rewards_per_episode))
            if self.rewards_per_episode
            else 0.0
        )

        # Expose to Prometheus
        rolling_avg_td_error_gauge.set(rolling_avg_td_error)

        stats = AgentEpisodeStats(
            episode_id=f"ep-{self.episode_count}",
            total_reward=total_reward,
            length=episode_steps,
            avg_reward=avg_reward,
            final_epsilon=self.qlearn_config.epsilon_current,
            rolling_avg_td_error=rolling_avg_td_error,
            rolling_avg_reward=rolling_avg_reward,
            max_abs_td_error_this_episode=max_abs_td_error,
            mean_td_error_this_episode=mean_td_error,
            start_time=self.env._episode_start_time
            if hasattr(self.env, "_episode_start_time")
            else None,  # type: ignore
        )

        logger.info("Episode completed", **stats.model_dump())

        self.q_agent.decay_epsilon()

        # Periodic checkpoint

        if self.episode_count % self.agent_config.checkpoint_interval == 0:
            metadata = TabularQCheckpointMetadata(
                created_at=datetime.now(timezone.utc),
                episode_count=self.episode_count,
                total_steps=self.total_steps,
                avg_reward_last_100=rolling_avg_reward,
                epsilon=self.qlearn_config.epsilon_current,
                rolling_avg_td_error=rolling_avg_td_error,
                source=CheckpointSource.EDGE,
            )

            success = save_tabular_checkpoint(
                q_table=self.q_agent.q_table,
                metadata=metadata,
                filepath=self.checkpoint_path,
            )

            stats.checkpoint_saved = success

            if success:
                logger.info(
                    "Checkpoint saved successfully",
                    episode=self.episode_count,
                    path=str(self.checkpoint_path),
                    rolling_avg_reward=rolling_avg_reward,
                    epsilon=self.qlearn_config.epsilon_current,
                )
            else:
                logger.warning(
                    "Checkpoint save failed - continuing without save",
                    episode=self.episode_count,
                    path=str(self.checkpoint_path),
                )

        return stats

    def load_checkpoint_if_exists(self) -> bool:
        """Load the latest checkpoint if the file exists.

        Returns:
            bool: True if a checkpoint was found and loaded, False otherwise
        """
        checkpoint_file = Path(self.checkpoint_path)
        if not checkpoint_file.exists():
            logger.info("No checkpoint file found", path=str(checkpoint_file))
            return False

        return self.q_agent.load_checkpoint(checkpoint_file)

    def save_checkpoint(
        self,
        episode_count: int,
        total_steps: int,
        avg_reward_last_100: float,
        source: Literal["edge", "central", "simulation"] = "edge",
    ) -> bool:
        """Save current Q-table state to checkpoint with metadata.

        Returns:
            bool: True if save succeeded
        """
        return self.q_agent.save_checkpoint(
            filepath=self.checkpoint_path,
            episode_count=episode_count,
            total_steps=total_steps,
            avg_reward_last_100=avg_reward_last_100,
            source=source,
        )
