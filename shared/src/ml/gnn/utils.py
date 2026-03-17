"""Utility functions for GNN processing and data preparation in Network-Chan.

These helpers support normalization, batching, graph preprocessing, and PyTorch Geometric
compatibility. Most are intended for the central Assistant (where PyTorch Geometric is
available), but lightweight utilities remain safe and importable on the edge Appliance.

All functions are pure (no side effects) and type-safe.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

from shared.src.config.shared_settings import settings

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Conditional imports for PyTorch Geometric (central Assistant only)
# ──────────────────────────────────────────────────────────────────────────────

if not settings.is_edge_device:
    try:
        import torch
        from torch_geometric.data import Batch, Data
    except ImportError:
        logger.warning(
            "torch or torch_geometric not available — PyG utilities disabled. "
            "This is expected on edge Appliance."
        )
        torch = None
        Data = None
        Batch = None
else:
    torch = None
    Data = None
    Batch = None


def normalize_node_features(
    data: Any,
    mean: Any | None = None,
    std: Any | None = None,
    eps: float = 1e-8,
) -> Any:
    """Normalize node features in-place (zero mean, unit variance).

    If mean/std are not provided, they are computed from the current data.
    Safe to call on edge (returns input unchanged if torch is unavailable).

    Args:
        data: torch_geometric.data.Data object (or dict-like with 'x' key)
        mean: Optional pre-computed mean tensor (shape [num_features])
        std: Optional pre-computed std tensor (shape [num_features])
        eps: Small value to avoid division by zero

    Returns:
        Normalized data object (same type as input)
    """
    if settings.is_edge_device or torch is None or Data is None:
        logger.debug("Normalization skipped on edge / missing torch")
        return data

    if not isinstance(data, Data) or data.x is None or data.x.numel() == 0:
        return data

    x = data.x

    if mean is None or std is None:
        mean = x.mean(dim=0, keepdim=True)
        std = x.std(dim=0, keepdim=True) + eps

    data.x = (x - mean) / std
    return data


def standardize_edge_attributes(
    data: Any,
    mean: Any | None = None,
    std: Any | None = None,
    eps: float = 1e-8,
) -> Any:
    """Normalize edge attributes in-place (if present).

    Similar to node feature normalization but for edge_attr.
    """
    if settings.is_edge_device or torch is None or Data is None:
        return data

    if (
        not isinstance(data, Data)
        or data.edge_attr is None
        or data.edge_attr.numel() == 0
    ):
        return data

    ea = data.edge_attr

    if mean is None or std is None:
        mean = ea.mean(dim=0, keepdim=True)
        std = ea.std(dim=0, keepdim=True) + eps

    data.edge_attr = (ea - mean) / std
    return data


def batch_graphs(graphs: List[Any]) -> Any:
    """Convert a list of Data objects to a single Batch (PyG).

    Safe on edge: returns input list unchanged if torch_geometric unavailable.
    """
    if settings.is_edge_device or Batch is None:
        logger.debug("Batching skipped on edge / missing torch_geometric")
        return graphs

    if not graphs:
        return Batch()

    try:
        return Batch.from_data_list(graphs)
    except Exception as e:
        logger.error("Failed to batch graphs: %s", e)
        return graphs


def add_self_loops(data: Any) -> Any:
    """Add self-loops to nodes with degree 0 (helps some GNN layers).

    Safe on edge: returns input unchanged.
    """
    if settings.is_edge_device or torch is None or Data is None:
        return data

    if not isinstance(data, Data) or data.edge_index is None or data.num_nodes == 0:
        return data

    from torch_geometric.utils import add_self_loops as pyg_add_self_loops

    edge_index, _ = pyg_add_self_loops(
        data.edge_index,
        num_nodes=data.num_nodes,
    )
    data.edge_index = edge_index
    return data


def ensure_consistent_feature_dim(
    data_list: List[Any],
    target_dim: int = 0,
) -> Tuple[List[Any], int]:
    """Ensure all graphs have the same node feature dimension.

    If target_dim is 0, uses the maximum dimension found in the list.
    Pads with zeros on missing dimensions (rare case).

    Returns:
        (updated list, final dimension)
    """
    if not data_list:
        return [], 0

    if settings.is_edge_device or torch is None:
        return data_list, len(data_list[0].get("x", [[]])[0]) if data_list[0].get(
            "x"
        ) else 0

    dims = [d.x.shape[1] if d.x is not None else 0 for d in data_list]
    max_dim = max(dims) if dims else 0
    target_dim = target_dim if target_dim > 0 else max_dim

    if max_dim == 0:
        return data_list, 0

    updated = []
    for d in data_list:
        if d.x is None or d.x.shape[1] == target_dim:
            updated.append(d)
            continue

        # Pad with zeros
        pad = torch.zeros(
            (d.num_nodes, target_dim - d.x.shape[1]),
            dtype=d.x.dtype,
            device=d.x.device,
        )
        d.x = torch.cat([d.x, pad], dim=1)
        updated.append(d)

    return updated, target_dim


def graph_summary(data: Any) -> Dict[str, Any]:
    """Lightweight summary stats for a graph (usable on edge or central).

    Safe and dependency-free.

    Returns:
        Dict with num_nodes, num_edges, avg_degree, etc.
    """
    if data is None:
        return {"num_nodes": 0, "num_edges": 0}

    if hasattr(data, "num_nodes") and hasattr(data, "num_edges"):
        # PyG Data object
        num_nodes = data.num_nodes
        num_edges = data.num_edges
    elif isinstance(data, dict) and "nodes" in data and "edges" in data:
        num_nodes = len(data["nodes"])
        num_edges = len(data["edges"])
    else:
        num_nodes = 0
        num_edges = 0

    if num_nodes == 0:
        return {"num_nodes": 0, "num_edges": 0, "avg_degree": 0.0}

    return {
        "num_nodes": num_nodes,
        "num_edges": num_edges,
        "avg_degree": num_edges / num_nodes if num_nodes > 0 else 0.0,
        "is_directed": False,  # assuming undirected for now
    }
