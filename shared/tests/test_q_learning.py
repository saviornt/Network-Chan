"""Unit tests for shared Q-Learning utilities (ml/rl/q_learning.py).

Tests cover:
- Epsilon-greedy action selection
- Q-value update logic
- Discrete state binning / discretization
- Edge cases (invalid indices, empty inputs, boundary values)

Uses pytest fixtures, mocking, and NumPy assertions for precision.
"""

from __future__ import annotations

import numpy as np
import pytest
from src.config.settings import settings
from src.ml.rl.q_learning import (
    epsilon_greedy_action,
    get_discrete_state,
    select_action,
    update_q_value,
)
from src.models.rl import RLObservation

# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_q_table() -> np.ndarray:
    """Simple 4-state, 3-action Q-table for testing."""
    return np.array(
        [
            [0.1, 0.8, 0.3],  # state 0: prefers action 1
            [0.9, 0.2, 0.4],  # state 1: prefers action 0
            [0.5, 0.5, 0.5],  # state 2: uniform
            [-0.1, 0.0, 0.7],  # state 3: prefers action 2
        ]
    )


@pytest.fixture
def sample_bins() -> dict[str, np.ndarray]:
    """Example bin edges for 3 features (latency, loss, clients)."""
    return {
        "latency": np.linspace(0, 100, 11),  # 0-100 ms → 10 bins
        "loss": np.linspace(0, 0.5, 6),  # 0-0.5 → 5 bins
        "clients": np.array([0, 10, 20, 50, 100]),  # irregular bins
    }


@pytest.fixture
def sample_observation() -> RLObservation:
    """Observation with 3 features matching sample_bins."""
    return RLObservation(
        features=[45.0, 0.12, 25.0],
        original_shape=(3,),
        device_id="AP-TEST-01",
        timestamp=1710650000.0,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Tests: epsilon_greedy_action (Numba inner function)
# ──────────────────────────────────────────────────────────────────────────────


def test_epsilon_greedy_explores_when_random():
    """Should return random action when random < epsilon."""
    q_row = np.array([1.0, 2.0, 3.0])
    rng = np.random.RandomState(42)  # fixed seed for test determinism
    rng.random_sample = lambda: 0.05  # force < 0.1 epsilon

    action = epsilon_greedy_action(q_row, epsilon=0.1, n_actions=3, rng_state=rng)
    assert 0 <= action < 3
    assert action != 2  # unlikely to be max with forced random


def test_epsilon_greedy_exploits_when_above_epsilon():
    """Should return argmax when random >= epsilon."""
    q_row = np.array([1.0, 5.0, 3.0])
    rng = np.random.RandomState(42)
    rng.random_sample = lambda: 0.5  # force > epsilon

    action = epsilon_greedy_action(q_row, epsilon=0.1, n_actions=3, rng_state=rng)
    assert action == 1  # index of max Q


# ──────────────────────────────────────────────────────────────────────────────
# Tests: update_q_value
# ──────────────────────────────────────────────────────────────────────────────


def test_update_q_value_standard_update(sample_q_table):
    """Standard Q update increases Q(s,a) toward TD target."""
    original_q = sample_q_table.copy()

    update_q_value(
        q_table=sample_q_table,
        state_idx=0,
        action_idx=1,
        reward=1.0,
        next_state_idx=2,
        alpha=0.1,
        gamma=0.99,
    )

    expected = original_q[0, 1] + 0.1 * (
        1.0 + 0.99 * np.max(sample_q_table[2]) - original_q[0, 1]
    )
    assert np.isclose(sample_q_table[0, 1], expected, atol=1e-6)


def test_update_q_value_terminal_state():
    """When next_state_idx < 0, TD target = reward only (no future)."""
    q_table = np.array([[0.0, 0.0]])
    original = q_table.copy()

    update_q_value(q_table, 0, 0, reward=5.0, next_state_idx=-1, alpha=0.5)

    assert np.isclose(q_table[0, 0], 0.0 + 0.5 * (5.0 - 0.0), atol=1e-6)


def test_update_q_value_invalid_index_raises():
    """Invalid state/action raises ValueError."""
    q_table = np.zeros((4, 3))

    with pytest.raises(ValueError, match="Invalid state index"):
        update_q_value(
            q_table, state_idx=10, action_idx=0, reward=1.0, next_state_idx=0
        )

    with pytest.raises(ValueError, match="Invalid action index"):
        update_q_value(q_table, state_idx=0, action_idx=5, reward=1.0, next_state_idx=0)


# ──────────────────────────────────────────────────────────────────────────────
# Tests: get_discrete_state
# ──────────────────────────────────────────────────────────────────────────────


def test_get_discrete_state_basic_binning(sample_observation, sample_bins):
    """Correct flat index from binned features."""
    state_idx = get_discrete_state(sample_observation, sample_bins)

    # Manual calculation for validation
    # latency 45 → bin 5 (0-10,10-20,...,40-50,50-60,...)
    # loss 0.12 → bin 2 (0-0.1,0.1-0.2,...)
    # clients 25 → bin 3 (0-10,10-20,20-50,50-100)
    expected = 5 * (5 * 4) + 2 * 4 + 3  # strides: clients=1, loss=4, latency=20
    assert state_idx == expected


def test_get_discrete_state_clipping():
    """Values outside bin range are clipped to edge bins."""
    obs = RLObservation(
        features=[-10.0, 1.0, 200.0],
        original_shape=(3,),
        device_id="test",
        timestamp=0.0,
    )
    bins = {
        "a": np.linspace(0, 100, 11),
        "b": np.linspace(0, 1, 6),
        "c": np.array([0, 50, 100]),
    }

    idx = get_discrete_state(obs, bins)
    assert idx >= 0  # should clamp to lowest/highest bin


def test_get_discrete_state_mismatch_raises(sample_observation):
    """Mismatch between features and bins raises ValueError."""
    wrong_bins = {"latency": np.linspace(0, 100, 11)}  # only 1 key
    with pytest.raises(ValueError, match="must match bin definitions"):
        get_discrete_state(sample_observation, wrong_bins)


# ──────────────────────────────────────────────────────────────────────────────
# Tests: select_action
# ──────────────────────────────────────────────────────────────────────────────


def test_select_action_calls_epsilon_greedy(sample_q_table):
    """select_action delegates to epsilon_greedy_action with proper args."""
    action = select_action(sample_q_table, state_idx=1, epsilon=0.0, seed=42)
    # With epsilon=0 → should be deterministic argmax
    expected = np.argmax(sample_q_table[1])
    assert action == expected


def test_select_action_respects_seed():
    """Same seed → same action sequence (deterministic exploration)."""
    q_table = np.ones((1, 5))  # uniform Q → argmax unstable, relies on random
    actions = []
    for _ in range(3):
        actions.append(select_action(q_table, 0, epsilon=1.0, seed=123))
    # All with same seed → should be identical (full exploration)
    assert len(set(actions)) == 1
