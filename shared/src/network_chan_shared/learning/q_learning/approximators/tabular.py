"""Tabular Q-function approximator using NumPy + Numba acceleration.

This module provides a simple, performant tabular Q-table implementation
suitable for small discrete state/action spaces (typical for early MVP
and edge Appliance usage).

All performance-critical paths are decorated with @njit for significant
speedup on both x86 and ARM (Raspberry Pi).
"""

from __future__ import annotations

import numpy as np
from numba import njit
from typing import Optional, Literal
from pathlib import Path
import datetime


from shared.settings.q_learning_settings import QLearningSettings
from shared.models.q_learning_models import Transition
from shared.models.rl_core_models import TabularQCheckpointMetadata
from shared.learning.q_learning.helper_functions import (
    compute_td_target,
    compute_td_error,
    update_q_table_value,
)
from shared.learning.q_learning.replay.uniform import UniformReplay
from shared.learning.q_learning.io.serialization import (
    save_tabular_checkpoint,
    load_tabular_checkpoint,
)
from shared.utils.logging_factory import get_logger

logger = get_logger("q_learning.approximators.tabular")


@njit
def _select_action_epsilon_greedy(
    q_table: np.ndarray,
    state: int,
    epsilon: float,
    n_actions: int,
) -> int:
    """Numba-accelerated ε-greedy action selection.

    Args:
        q_table: 2D numpy array [n_states, n_actions]
        state: Current state index
        epsilon: Probability of random action
        n_actions: Total number of actions

    Returns:
        Selected action index
    """
    if np.random.random() < epsilon:
        return np.random.randint(0, n_actions)
    return int(np.argmax(q_table[state]))


class TabularQ:
    """Tabular Q-function approximator with integrated replay and checkpointing.

    Attributes:
        q_table: numpy.ndarray of shape (n_states, n_actions)
        config: Shared Q-Learning settings
        replay: Uniform replay buffer for experience storage
    """

    def __init__(
        self,
        config: QLearningSettings,
        replay_capacity: int = 10_000,
    ):
        """Initialize tabular Q-function with replay buffer.

        Args:
            config: Shared Q-Learning settings
            replay_capacity: Max transitions to store (default 10k for edge)
        """
        self.config = config
        self.q_table = np.zeros(
            (config.default_n_states, config.default_n_actions), dtype=np.float32
        )
        self.replay = UniformReplay(capacity=replay_capacity)

    @property
    def n_states(self) -> int:
        """Number of states in the current Q-table."""
        return self.q_table.shape[0]

    @property
    def n_actions(self) -> int:
        """Number of actions in the current Q-table."""
        return self.q_table.shape[1]

    def update_from_transition(self, transition: Transition) -> float:
        """Perform one Q-value update from a transition using core helpers + Numba.

        Logs any issues but does not raise.

        Args:
            transition: Validated Transition model

        Returns:
            TD error (or 0.0 on invalid input)
        """
        if not (
            isinstance(transition.state, int) and isinstance(transition.next_state, int)
        ):
            logger.error(
                "Non-integer states passed to tabular update - skipping",
                state_type=type(transition.state).__name__,
                next_state_type=type(transition.next_state).__name__,
                transition=transition.model_dump(),
            )
            return 0.0

        # Compute target using shared helper
        next_value = (
            np.max(self.q_table[transition.next_state]) if not transition.done else 0.0
        )
        td_target = compute_td_target(
            reward=transition.reward,
            next_state_value=next_value,
            done=transition.done,
            gamma=self.config.gamma,
        )

        current_q = self.q_table[transition.state, transition.action]
        td_error = compute_td_error(current_q=current_q, td_target=td_target)

        # Apply update with Numba acceleration
        update_q_table_value(
            self.q_table,
            transition.state,
            transition.action,
            td_error,
            self.config.alpha,
        )

        # Store in replay for batch/offline use
        self.replay.add(transition)

        logger.info(
            "Q-value updated",
            state=transition.state,
            action=transition.action,
            td_error=td_error,
            td_target=td_target,
            reward=transition.reward,
        )

        return td_error

    def select_action(self, state: int, epsilon: Optional[float] = None) -> int:
        """Select an action using ε-greedy policy.

        Args:
            state: Current integer state index
            epsilon: Override exploration rate (defaults to current config value)

        Returns:
            Selected action index
        """
        if epsilon is None:
            epsilon = self.config.epsilon_current

        action = _select_action_epsilon_greedy(
            self.q_table,
            state,
            epsilon,
            self.n_actions,
        )

        logger.debug(
            "Action selected",
            state=state,
            action=action,
            epsilon=epsilon,
            is_exploratory=(epsilon > 0.0),
        )
        return action

    def decay_epsilon(self) -> None:
        """Apply one step of epsilon decay using configured schedule."""
        self.config.decay_epsilon()
        logger.debug("Epsilon decayed", current=self.config.epsilon_current)

    def save_checkpoint(
        self,
        filepath: str | Path,
        episode_count: int,
        total_steps: int,
        avg_reward_last_100: float,
        source: Literal["edge", "central", "simulation"] = "edge",
    ) -> bool:
        """Save current Q-table state to checkpoint with metadata.

        Returns success flag (logged on failure).
        """
        metadata = TabularQCheckpointMetadata(
            created_at=datetime.datetime.now(datetime.timezone.utc),
            episode_count=episode_count,
            total_steps=total_steps,
            avg_reward_last_100=avg_reward_last_100,
            epsilon=self.config.epsilon_current,
            source=source,
        )

        success = save_tabular_checkpoint(
            q_table=self.q_table,
            metadata=metadata,
            filepath=filepath,
        )

        if success:
            logger.info("Checkpoint saved", filepath=str(filepath))
        return success

    def load_checkpoint(self, filepath: str | Path) -> bool:
        """Load Q-table from checkpoint file (with fallback on failure).

        Returns True if loaded successfully, False if fallback used.
        """
        try:
            q_table, metadata = load_tabular_checkpoint(filepath)
            self.q_table = q_table
            logger.info(
                "Checkpoint loaded successfully",
                filepath=str(filepath),
                episode_count=metadata.episode_count,
                source=metadata.source,
            )
            return True
        except Exception as e:
            logger.exception(
                "Failed to load checkpoint - using current state",
                error_type=type(e).__name__,
                error_msg=str(e),
                filepath=str(filepath),
            )
            return False
