# appliance/src/meta_learner.py

from typing import List, Dict, Any, Union
import asyncio
import numpy as np
from numba import jit # type: ignore

@jit(nopython=True) # type: ignore[misc]
def compute_gradient_update(params: np.ndarray, grads: np.ndarray, lr: float = 0.01) -> np.ndarray:  # Numba for vector updates
    return params - lr * grads  # Placeholder SGD

class ReptileMetaLearner:
    def __init__(self, param_dim: int = 100, inner_lr: float = 0.01, outer_lr: float = 0.001) -> None:
        self.param_dim: int = param_dim
        self.inner_lr: float = inner_lr
        self.outer_lr: float = outer_lr
        self.params: np.ndarray = np.zeros(param_dim)  # Mock model params

    async def adapt_to_tasks(self, tasks: List[Dict[str, Any]]) -> None:  # tasks: List of {'data': np.ndarray, 'labels': np.ndarray}
        loop = asyncio.get_running_loop()
        tasks_coros: List[asyncio.Task[np.ndarray]] = [loop.create_task(self._inner_loop(task)) for task in tasks]
        adapted_params: List[Union[np.ndarray, BaseException]] = await asyncio.gather(*tasks_coros, return_exceptions=True)
        valid_params: List[np.ndarray] = [p for p in adapted_params if not isinstance(p, BaseException)]
        if valid_params:
            # Outer update: Average adaptations
            avg_params: np.ndarray = np.mean(valid_params, axis=0)
            self.params = self.params + self.outer_lr * (avg_params - self.params)

    async def _inner_loop(self, task: Dict[str, Any]) -> np.ndarray:
        await asyncio.sleep(0)
        if not isinstance(task.get('data'), np.ndarray):
            raise ValueError("Invalid task data type")
        mock_grads: np.ndarray = np.random.rand(self.param_dim)
        return compute_gradient_update(self.params, mock_grads, self.inner_lr)

# Usage stub
async def main() -> None:
    learner = ReptileMetaLearner()
    mock_tasks: List[Dict[str, Any]] = [{'data': np.random.rand(10), 'labels': np.random.rand(10)} for _ in range(3)]
    await learner.adapt_to_tasks(mock_tasks)
    print(f"Updated params mean: {np.mean(learner.params)}")

if __name__ == "__main__":
    asyncio.run(main())