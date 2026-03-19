"""Pure helper functions for Q-Learning operations.

This module contains stateless, pure functions that operate on Q-values,
transitions, or configuration values. They are intended to be reused
across different approximators (tabular, MLP, future GNN) and contexts
(edge inference, central training, simulation).

All functions here should:
- Be pure (no side effects, no I/O)
- Be easily testable in isolation
- Support @njit where performance-critical
"""

from __future__ import annotations

import numpy as np
from numba import njit


@njit
def compute_td_target(
    reward: float,
    next_state_value: float,
    done: bool,
    gamma: float,
) -> float:
    """Compute the TD target (Bellman target) for a single transition.

    Args:
        reward: Scalar reward
        next_state_value: Value estimate of the next state (max Q or V)
        done: Whether the episode terminated
        gamma: Discount factor

    Returns:
        The target value for the current state-action pair
    """
    if done:
        return reward
    return reward + gamma * next_state_value


@njit
def compute_td_error(
    current_q: float,
    td_target: float,
) -> float:
    """Compute temporal difference error.

    Args:
        current_q: Current Q-value estimate for (s,a)
        td_target: Computed target value

    Returns:
        TD error (target - current)
    """
    return td_target - current_q


@njit
def update_q_table_value(
    q_table: np.ndarray,
    state: int,
    action: int,
    td_error: float,
    alpha: float,
) -> None:
    """Numba-accelerated single Q-value update."""
    q_table[state, action] += alpha * td_error


def apply_epsilon_decay(
    current_epsilon: float,
    epsilon_min: float,
    epsilon_decay: float,
) -> float:
    """Apply one step of epsilon decay (non-Numba, since not hot path).

    Args:
        current_epsilon: Current exploration rate
        epsilon_min: Floor value
        epsilon_decay: Multiplicative decay factor

    Returns:
        New epsilon value
    """
    return max(epsilon_min, current_epsilon * epsilon_decay)


def get_action_probs_from_logits(
    logits: np.ndarray,
    temperature: float = 1.0,
) -> np.ndarray:
    """Softmax over action logits with temperature (for future policy-based methods).

    Args:
        logits: Array of action values / logits [n_actions]
        temperature: Softmax temperature (>0)

    Returns:
        Probability distribution over actions
    """
    if temperature <= 0:
        raise ValueError("Temperature must be > 0")

    exp_logits = np.exp(logits / temperature)
    return exp_logits / np.sum(exp_logits)


# Future helpers can be added here, e.g.:
# - n_step_returns(...)
# - double_q_target(...)
# - huber_loss(...)
# - clipped_reward(...)
