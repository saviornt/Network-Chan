"""Dummy network environment for Q-Learning testing on the Appliance.

Simulates a very simple discrete network with 16 states (4×4 grid zones)
and 4 actions. Used for local testing before integrating real telemetry
and Netmiko/Omada API calls.

States: 0–15 (flattened grid coordinates)
Actions: 0=adjust_channel, 1=throttle, 2=rebalance, 3=noop

Reward: -latency - loss + balance_bonus
"""

from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Tuple

from shared.models.q_learning_models import Transition
from shared.utils.logging_factory import get_logger

logger = get_logger("q_learning.dummy_env")


class DummyNetworkEnv:
    """Simple discrete dummy environment mimicking network dynamics."""

    def __init__(
        self, n_states: int = 16, n_actions: int = 4, max_steps_per_episode: int = 200
    ):
        """Initialize dummy network environment.

        Args:
            n_states: Total discrete states (default 16 = 4×4 grid)
            n_actions: Total discrete actions (default 4)
            max_steps_per_episode: Maximum steps before forcing episode end
        """
        self.n_states = n_states
        self.n_actions = n_actions
        self.max_steps_per_episode = max_steps_per_episode

        self.current_state: int = 0
        self.step_count: int = 0
        self._episode_start_time: datetime | None = None

        self.reset()  # Initialize with first episode start time

        logger.info(
            "Dummy network environment initialized",
            n_states=n_states,
            n_actions=n_actions,
            max_steps=self.max_steps_per_episode,
        )

    def reset(self) -> int:
        """Reset environment to random initial state and record episode start time.

        Returns:
            Initial state index
        """
        self.current_state = random.randint(0, self.n_states - 1)
        self.step_count = 0
        self._episode_start_time = datetime.now(timezone.utc)

        logger.debug(
            "Environment reset",
            initial_state=self.current_state,
            episode_start_time=self._episode_start_time.isoformat(),
        )
        return self.current_state

    def step(self, action: int) -> Tuple[int, float, bool]:
        """Execute one step: take action, compute reward, transition state.

        Args:
            action: Integer action index (0–3)

        Returns:
            Tuple of (next_state, reward, done)
        """
        self.step_count += 1

        # Simple transition: move "forward" with noise
        next_state = (self.current_state + random.randint(-1, 2)) % self.n_states

        # Dummy reward calculation
        latency = random.uniform(10, 50)  # ms
        packet_loss = random.uniform(0.0, 0.05)  # fraction
        balance_bonus = -abs((next_state % 4) - 2) * 5  # prefer middle zones

        reward = -latency * 0.01 - packet_loss * 100 + balance_bonus

        # Action effect (toy example)
        if action == 0:  # adjust_channel
            reward += 15.0
        elif action == 1:  # throttle
            reward += 5.0 - packet_loss * 50
        elif action == 2:  # rebalance
            reward += 10.0 + balance_bonus * 2
        # action 3 = noop → no bonus

        done = self.step_count >= self.max_steps_per_episode

        logger.debug(
            "Dummy step executed",
            action=action,
            from_state=self.current_state,
            to_state=next_state,
            reward=reward,
            done=done,
            step=self.step_count,
        )

        self.current_state = next_state
        return next_state, reward, done

    @property
    def episode_start_time(self) -> datetime:
        """UTC start time of the current episode."""
        if self._episode_start_time is None:
            logger.warning("Episode start time accessed before reset")
            return datetime.now(timezone.utc)
        return self._episode_start_time

    def get_random_transition(self) -> Transition:
        """Generate a random transition for testing."""
        state = random.randint(0, self.n_states - 1)
        action = random.randint(0, self.n_actions - 1)
        next_state, reward, done = self.step(action)
        return Transition(
            state=state,
            action=action,
            reward=reward,
            next_state=next_state,
            done=done,
        )
