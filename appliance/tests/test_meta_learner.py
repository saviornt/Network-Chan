# appliance/tests/test_meta_learner.py

import pytest
import numpy as np
from appliance.src.ml.reptile_maml import ReptileMetaLearner, compute_gradient_update

@pytest.mark.asyncio
async def test_adapt_to_tasks() -> None:
    learner = ReptileMetaLearner(param_dim=2, inner_lr=0.1, outer_lr=0.05)
    mock_tasks = [{'data': np.random.rand(10), 'labels': np.random.rand(10)} for _ in range(2)]
    await learner.adapt_to_tasks(mock_tasks)
    assert learner.params.shape == (2,)  # Params updated
    assert not np.allclose(learner.params, np.zeros(2))  # Changed from init

def test_compute_gradient_update_numba() -> None:
    params = np.array([1.0, 2.0])
    grads = np.array([0.5, 1.0])
    lr = 0.1
    updated = compute_gradient_update(params, grads, lr)
    expected = params - lr * grads
    np.testing.assert_array_equal(updated, expected)

@pytest.mark.asyncio
async def test_adapt_to_tasks_empty() -> None:
    learner = ReptileMetaLearner()
    await learner.adapt_to_tasks([])  # No change
    np.testing.assert_array_equal(learner.params, np.zeros(learner.param_dim))

@pytest.mark.asyncio
async def test_adapt_to_tasks_with_error() -> None:
    learner = ReptileMetaLearner()
    mock_tasks = [{'data': 'invalid'}]  # Triggers raise in _inner_loop
    await learner.adapt_to_tasks(mock_tasks)
    # Since exceptions are skipped, check no update (params unchanged)
    np.testing.assert_array_equal(learner.params, np.zeros(learner.param_dim))  # No valid params, no change