# appliance/tests/test_tiny_gnn.py
from unittest.mock import patch

import numpy as np
import pytest

from appliance.src.learning.tiny_gnn import TinyGNN, gnn_forward


@pytest.mark.asyncio
async def test_load_model() -> None:
    gnn = TinyGNN()
    await gnn.load_model("test_path")
    assert gnn.model is not None
    assert gnn.model.shape == (gnn.hidden_dim, gnn.node_dim)


@pytest.mark.asyncio
async def test_embed_graph() -> None:
    gnn = TinyGNN(node_dim=3, hidden_dim=4)
    features: np.ndarray = np.random.rand(2, 3)
    adjacency: np.ndarray = np.random.rand(2, 2)
    embedding = await gnn.embed_graph(features, adjacency)
    assert embedding.shape == (2, 4)  # After mock layer


@pytest.mark.asyncio
async def test_embed_graph_empty() -> None:
    gnn = TinyGNN()
    features: np.ndarray = np.empty((0, 5))
    adjacency: np.ndarray = np.empty((0, 0))
    embedding = await gnn.embed_graph(features, adjacency)
    assert embedding.size == 0
    assert embedding.shape == (0, 0)  # Consistent empty


@pytest.mark.asyncio
async def test_embed_graph_no_model() -> None:
    gnn = TinyGNN()
    # Patch load to do nothing, force no model branch
    with patch.object(gnn, "load_model", return_value=None):
        features = np.random.rand(2, 3)
        adjacency = np.eye(2)
        embedding = await gnn.embed_graph(features, adjacency)
    assert gnn.model is None  # Not loaded
    assert embedding.shape == (2, 3)  # Unchanged from forward (no model dot)


@pytest.mark.asyncio
async def test_embed_graph_shape_mismatch() -> None:
    gnn = TinyGNN(node_dim=3, hidden_dim=4)
    features = np.random.rand(2, 3)
    adjacency = np.random.rand(3, 3)  # Mismatch (3x3 vs 2 nodes)
    embedding = await gnn.embed_graph(features, adjacency)
    assert embedding.shape == (2, 4)  # Fallback identity fixes


def test_gnn_forward_numba() -> None:
    features: np.ndarray = np.array([[1.0, 2.0], [3.0, 4.0]])
    adjacency: np.ndarray = np.array([[0.0, 1.0], [1.0, 0.0]])
    result = gnn_forward(features, adjacency)
    np.testing.assert_array_equal(result, np.array([[3.0, 4.0], [1.0, 2.0]]))


def test_gnn_forward_empty() -> None:
    features: np.ndarray = np.empty((0, 0))
    adjacency: np.ndarray = np.empty((0, 0))
    result = gnn_forward(features, adjacency)
    assert result.size == 0
    assert result.shape == (0, 0)


def test_gnn_forward_shape_mismatch() -> None:
    features = np.array([[1.0]])
    adjacency = np.array([[0.0, 1.0]])  # 1x2 vs 1x1
    result = gnn_forward(features, adjacency)
    assert result.size == 0
    assert result.shape == (0, 0)
