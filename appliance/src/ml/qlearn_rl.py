# appliance/src/edge_rl.py

import asyncio

import numpy as np  # For states/actions; install later
from numba import jit  # type: ignore
from numba import types as numba_types


# Numba signature for typed dict-like (mock Q-table as array for perf)
@jit(numba_types.float64(numba_types.float64[:], numba_types.int64))  # type: ignore[attr-defined]
def get_q_value(state: np.ndarray, action: int) -> float:
    if state.size == 0:
        return 0.0
    return action * np.mean(state)  # type: ignore | Adjusted: Allows negative if state negative; testable


class QLearningAgent:
    def __init__(self, state_dim: int = 10, action_dim: int = 5, alpha: float = 0.1, gamma: float = 0.99) -> None:
        self.state_dim: int = state_dim
        self.action_dim: int = action_dim
        self.alpha: float = alpha  # Learning rate
        self.gamma: float = gamma  # Discount
        self.q_table: dict[tuple[float, ...], list[float]] = {}  # Mock dict; use np array later

    async def select_action(self, state: np.ndarray) -> int:
        await asyncio.sleep(0)  # Async yield for concurrency
        q_values: list[float] = [get_q_value(state, a) for a in range(self.action_dim)]
        return int(np.argmax(q_values))  # Greedy select

    async def update(self, state: np.ndarray, action: int, reward: float, next_state: np.ndarray) -> None:
        await asyncio.sleep(0)
        state_tuple: tuple[float, ...] = tuple(state)
        if state_tuple not in self.q_table:
            self.q_table[state_tuple] = [0.0] * self.action_dim
        current_q: float = self.q_table[state_tuple][action]
        next_action: int = await self.select_action(next_state)
        next_q: float = get_q_value(next_state, next_action)
        new_q: float = current_q + self.alpha * (reward + self.gamma * next_q - current_q)
        self.q_table[state_tuple][action] = new_q


# Usage stub
async def main() -> None:
    agent = QLearningAgent()
    state: np.ndarray = np.random.rand(10)
    action: int = await agent.select_action(state)
    print(f"Selected action: {action}")
    await agent.update(state, action, 1.0, np.random.rand(10))


if __name__ == "__main__":
    asyncio.run(main())