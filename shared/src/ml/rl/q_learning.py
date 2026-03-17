"""Shared Q-Learning utilities for Network-Chan RL.

This module implements core Q-Learning components that can run on both:
- Appliance (edge inference, lightweight table updates)
- Assistant (central training, simulation, policy improvement)

Uses Numba for performance-critical operations (Q-update, epsilon-greedy selection).
All functions are pure or take explicit parameters — no global state.
"""

from __future__ import annotations

from typing import Dict, List

import numba as nb
import numpy as np

from src.config.settings import Settings
from src.models.rl import RLObservation


@nb.njit(fastmath=True, cache=True)
def epsilon_greedy_action(
    q_table_row: np.ndarray,
    epsilon: float,
    n_actions: int,
    rng_state: np.random.RandomState,
) -> np.int64:
    """Select action using epsilon-greedy policy (Numba-accelerated)."""
    if rng_state.random_sample() < epsilon:
        return np.int64(rng_state.randint(0, n_actions))
    else:
        return np.int64(np.argmax(q_table_row))


def update_q_value(
    q_table: np.ndarray,
    state_idx: int,
    action_idx: int,
    reward: float,
    next_state_idx: int,
    alpha: float = Settings().rl_alpha,
    gamma: float = 0.99,
) -> None:
    """Perform single Q-Learning update (off-policy TD)."""
    if state_idx < 0 or state_idx >= q_table.shape[0]:
        raise ValueError(f"Invalid state index: {state_idx}")
    if action_idx < 0 or action_idx >= q_table.shape[1]:
        raise ValueError(f"Invalid action index: {action_idx}")

    max_next_q = np.max(q_table[next_state_idx]) if next_state_idx >= 0 else 0.0
    td_target = reward + gamma * max_next_q
    q_table[state_idx, action_idx] += alpha * (
        td_target - q_table[state_idx, action_idx]
    )


def get_discrete_state(
    obs: RLObservation,
    bins: Dict[str, np.ndarray],
) -> int:
    """Discretize continuous observation into a single state index for tabular Q-Learning."""
    if len(obs.features) != len(bins):
        raise ValueError("Observation features length must match bin definitions")

    indices: List[int] = []
    for i, (_, feature_bins) in enumerate(bins.items()):
        val = obs.features[i]
        idx = np.digitize(val, feature_bins) - 1
        idx = int(np.clip(idx, 0, len(feature_bins) - 2))
        indices.append(idx)

    # Compute flat index
    strides = np.cumprod([len(b) - 1 for b in bins.values()][::-1])[::-1]
    strides = np.insert(strides, 0, 1)[:-1]
    state_idx = sum(i * s for i, s in zip(indices, strides, strict=False))

    return int(state_idx)  # explicit cast to satisfy Pylance


def select_action(
    q_table: np.ndarray,
    state_idx: int,
    epsilon: float = 0.1,
    seed: int | None = None,
) -> np.int64:
    """Select action using epsilon-greedy (Numba inside)."""
    rng = np.random.RandomState(seed) if seed is not None else np.random.RandomState()
    return epsilon_greedy_action(
        q_table[state_idx],
        epsilon,
        q_table.shape[1],
        rng,
    )
