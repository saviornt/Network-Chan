# appliance/tests/test_edge_rl.py

import numpy as np
import pytest

from appliance.src.ml.qlearn_rl import QLearningAgent, get_q_value


@pytest.mark.asyncio
async def test_select_action() -> None:
    agent = QLearningAgent(state_dim=3, action_dim=2)
    state = np.array([1.0, 2.0, 3.0])
    action = await agent.select_action(state)
    assert 0 <= action < agent.action_dim
    # Mock expected (based on get_q_value sum + action)
    expected_action = 1  # Since action 1 adds more
    assert action == expected_action


@pytest.mark.asyncio
async def test_update() -> None:
    agent = QLearningAgent(state_dim=3, action_dim=2, alpha=0.5, gamma=0.9)
    state = np.array([1.0, 1.0, 1.0])
    action = 0
    reward = 1.0
    next_state = np.array([1.0, 1.0, 1.0])
    await agent.update(state, action, reward, next_state)
    state_tuple = tuple(state)
    assert state_tuple in agent.q_table
    assert len(agent.q_table[state_tuple]) == agent.action_dim
    # Updated expected: With get_q_value = action * mean(state=1.0)
    # next_action=1 (max 1*1 > 0*1), next_q=1
    expected_q = 0 + 0.5 * (1.0 + 0.9 * 1 - 0)  # 0.5 * 1.9 = 0.95
    assert agent.q_table[state_tuple][action] == pytest.approx(expected_q)  # type: ignore


def test_get_q_value_numba() -> None:
    state = np.array([1.0, 2.0])
    action = 1
    assert get_q_value(state, action) == action * np.mean(state)  # Should match logic


@pytest.mark.asyncio
async def test_update_new_state() -> None:
    agent = QLearningAgent(state_dim=2, action_dim=2)
    state = np.array([0.5, 0.5])
    await agent.update(state, 0, 1.0, np.array([1.0, 1.0]))
    state_tuple = tuple(state)
    assert state_tuple in agent.q_table
    assert agent.q_table[state_tuple][0] > 0  # Updated positively


@pytest.mark.asyncio
async def test_update_negative_reward() -> None:
    agent = QLearningAgent()
    state = np.array([1.0] * agent.state_dim)
    await agent.update(state, 0, -10.0, np.array([-1.0] * agent.state_dim))  # Negative state for next_q <0
    assert agent.q_table[tuple(state)][0] < 0