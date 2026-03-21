"""Uniform (FIFO/circular) replay buffer for Q-Learning and off-policy RL.

This is a simple, memory-efficient buffer that stores transitions in a
fixed-size circular array. When full, oldest transitions are overwritten.

Suitable for both edge (Appliance - low memory) and central (Assistant - larger
replay for batch training) usage. No prioritization or fancy sampling yet —
uniform random sampling only.
"""

from __future__ import annotations

import random
from collections import deque
from typing import List, Tuple, Dict, Any

import numpy as np
from numpy.typing import NDArray

from shared.models.q_learning_models import Transition


class UniformReplay:
    """Uniform circular replay buffer for storing and sampling transitions.

    Uses a fixed-size deque for O(1) append/pop from both ends.
    Supports batch sampling with or without replacement.

    Attributes:
        capacity: Maximum number of transitions to store
        buffer: Internal storage (deque of Transition objects)
        size: Current number of stored transitions
    """

    def __init__(self, capacity: int):
        """Initialize the replay buffer.

        Args:
            capacity: Maximum number of transitions to store (fixed size)
        """
        if capacity <= 0:
            raise ValueError("Buffer capacity must be positive")

        self.capacity = capacity
        self.buffer: deque[Transition] = deque(maxlen=capacity)
        self._size: int = 0

    @property
    def size(self) -> int:
        """Current number of stored transitions."""
        return len(self.buffer)

    @property
    def is_full(self) -> bool:
        """True if buffer has reached capacity."""
        return self.size >= self.capacity

    def add(self, transition: Transition) -> None:
        """Add a single transition to the buffer.

        If full, oldest transition is automatically dropped (FIFO).

        Args:
            transition: Validated Transition model to store
        """
        self.buffer.append(transition)
        self._size = len(self.buffer)

    def add_batch(self, transitions: List[Transition]) -> None:
        """Add multiple transitions at once (more efficient)."""
        for t in transitions:
            self.add(t)

    def sample(self, batch_size: int, replace: bool = False) -> List[Transition]:
        """Sample a batch of transitions uniformly at random.

        Args:
            batch_size: Number of transitions to return
            replace: If True, sample with replacement (allows duplicates)

        Returns:
            List of randomly sampled Transition objects

        Raises:
            ValueError: If batch_size > current size and replace=False
        """
        if batch_size <= 0:
            raise ValueError("Batch size must be positive")

        current_size = self.size
        if current_size == 0:
            raise ValueError("Cannot sample from empty buffer")

        if batch_size > current_size and not replace:
            raise ValueError(
                f"Cannot sample {batch_size} without replacement from buffer of size {current_size}"
            )

        if replace:
            indices = random.choices(range(current_size), k=batch_size)
        else:
            indices = random.sample(
                range(current_size), k=min(batch_size, current_size)
            )

        return [self.buffer[i] for i in indices]

    def sample_numpy_arrays(
        self,
        batch_size: int,
        replace: bool = False,
        include_done: bool = True,
    ) -> Tuple[
        NDArray[np.int32],
        NDArray[np.int32],
        NDArray[np.float32],
        NDArray[np.int32],
        NDArray[np.bool_],
    ]:
        """Sample batch and return as separate NumPy arrays (fast for training).

        Args:
            batch_size: Number of samples
            replace: Sample with replacement if True
            include_done: Include done flags in output

        Returns:
            Tuple of (states, actions, rewards, next_states, dones)
            All as 1D/2D NumPy arrays (assuming integer states/actions)
        """
        samples = self.sample(batch_size, replace=replace)

        states = np.array([t.state for t in samples], dtype=np.int32)
        actions = np.array([t.action for t in samples], dtype=np.int32)
        rewards = np.array([t.reward for t in samples], dtype=np.float32)
        next_states = np.array([t.next_state for t in samples], dtype=np.int32)
        dones = (
            np.array([t.done for t in samples], dtype=np.bool_)
            if include_done
            else None
        )

        if include_done:
            dones = np.array([t.done for t in samples], dtype=np.bool_)
        else:
            dones = np.zeros(batch_size, dtype=np.bool_)

        return states, actions, rewards, next_states, dones

    def clear(self) -> None:
        """Remove all transitions from the buffer."""
        self.buffer.clear()
        self._size = 0

    def get_stats(self) -> Dict[str, Any]:
        """Basic statistics for observability (Prometheus/MQTT reporting)."""
        if self.size == 0:
            return {"size": 0, "avg_reward": 0.0}

        rewards = [t.reward for t in self.buffer]
        return {
            "size": self.size,
            "capacity": self.capacity,
            "avg_reward": float(np.mean(rewards)),
            "max_reward": float(np.max(rewards)),
            "min_reward": float(np.min(rewards)),
        }
