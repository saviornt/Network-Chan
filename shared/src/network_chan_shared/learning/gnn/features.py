"""Graph feature extraction utilities for GNN-based topology reasoning in Network-Chan.

This module transforms network telemetry, observations, and known topology data
into graph structures suitable for PyTorch Geometric (PyG) models on the central
Assistant. On the edge (Appliance), only lightweight graph snapshots are maintained.

Nodes: devices (routers, switches, APs, clients)
Edges: wired links, wireless associations, routing paths
Node features: telemetry metrics (CPU, temperature, client count, latency, etc.)
Edge features: link utilization, packet loss, bandwidth

The heavy PyG export is guarded and only available on the Assistant.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

import networkx as nx

from ...utils import check_device
from ...models.rl_core_models import RLObservation

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Conditional imports for PyTorch Geometric (central Assistant only)
# ──────────────────────────────────────────────────────────────────────────────

if not check_device.is_edge_device:
    try:
        import torch
        from torch_geometric.data import Data
    except ImportError:
        logger.warning(
            "torch or torch_geometric not available — PyG export disabled. "
            "This is expected on edge Appliance."
        )
        torch = None
        Data = None
else:
    torch = None
    Data = None


class TopologyGraphBuilder:
    """Builder for network topology graphs from observations and device data.

    Maintains a NetworkX graph internally.
    Supports incremental updates for real-time use.
    Can export to PyTorch Geometric Data (Assistant only).
    """

    def __init__(self) -> None:
        """Initialize empty topology graph."""
        self.graph: nx.Graph = nx.Graph()
        self.node_id_map: Dict[str, int] = {}  # device_id → consecutive integer index
        self.next_node_idx: int = 0

    def add_or_update_device(
        self,
        device_id: str,
        device_type: str | None = None,
        features: Dict[str, Any] | None = None,
    ) -> int:
        """Add or update a node (device) with features.

        If device_type is None, attempts to infer from device_id or features.

        Args:
            device_id: Unique identifier (MAC, IP, AP name, etc.)
            device_type: Optional explicit type ('router', 'switch', 'ap', 'client')
            features: Optional dict of numeric/categorical node features

        Returns:
            Integer node index in the graph
        """
        if device_id not in self.node_id_map:
            # Infer type if not provided
            if device_type is None:
                device_type = self._infer_device_type(device_id, features)

            self.node_id_map[device_id] = self.next_node_idx
            node_data = {
                "device_id": device_id,
                "type": device_type or "unknown",
            }
            if features:
                node_data.update(features)
            self.graph.add_node(self.next_node_idx, **node_data)
            self.next_node_idx += 1
        else:
            idx = self.node_id_map[device_id]
            if features:
                self.graph.nodes[idx].update(features)
            if device_type and self.graph.nodes[idx].get("type") == "unknown":
                self.graph.nodes[idx]["type"] = device_type

        return self.node_id_map[device_id]

    def _infer_device_type(
        self, device_id: str, features: Dict[str, Any] | None
    ) -> str:
        """Basic heuristic to infer device type from ID or features."""
        dev_id_lower = device_id.lower()
        if "ap" in dev_id_lower or "wifi" in dev_id_lower:
            return "ap"
        if "router" in dev_id_lower or "gw" in dev_id_lower:
            return "router"
        if "switch" in dev_id_lower:
            return "switch"
        if features and "client_count" in features and features["client_count"] == 0:
            return "client"
        return "unknown"

    def add_link(
        self,
        source_id: str,
        target_id: str,
        bidirectional: bool = True,
        features: Dict[str, Any] | None = None,
    ) -> None:
        """Add an edge (link) between two devices.

        Args:
            source_id: Source device ID
            target_id: Target device ID
            bidirectional: Add reverse edge (default True for undirected)
            features: Optional edge attributes (utilization, loss_rate, etc.)
        """
        if source_id not in self.node_id_map or target_id not in self.node_id_map:
            raise ValueError("Both devices must be added before creating a link")

        src_idx = self.node_id_map[source_id]
        tgt_idx = self.node_id_map[target_id]

        edge_data = features or {}
        self.graph.add_edge(src_idx, tgt_idx, **edge_data)

        if bidirectional and not self.graph.has_edge(tgt_idx, src_idx):
            self.graph.add_edge(tgt_idx, src_idx, **edge_data)

    def from_observation_batch(
        self,
        observations: List[RLObservation],
        device_info: Dict[
            str, Dict[str, Any]
        ],  # device_id → {"type": str, "features": dict}
        infer_links: bool = True,
    ) -> None:
        """Batch-update graph from multiple RL observations.

        Args:
            observations: List of observations from different devices
            device_info: Mapping of device_id → metadata (type, features)
            infer_links: If True, attempt to infer simple neighbor links from data
        """
        for obs in observations:
            dev_id = obs.device_id
            info = device_info.get(dev_id, {})
            self.add_or_update_device(
                device_id=dev_id,
                device_type=info.get("type"),
                features=info.get("features", {}),
            )

        if infer_links:
            self._infer_links_from_observations(observations)

    def _infer_links_from_observations(self, observations: List[RLObservation]) -> None:
        """TODO: Implement simple link inference from observation metadata.

        Current limitations: RLObservation does not yet contain neighbor lists.
        Future: extend RLObservation with 'neighbors' or 'routing_table' field.
        """
        # Placeholder — real implementation depends on observation schema evolution
        # Example future logic:
        # for obs in observations:
        #     if hasattr(obs, 'neighbors') and obs.neighbors:
        #         for neighbor_id in obs.neighbors:
        #             self.add_link(obs.device_id, neighbor_id)

        logger.debug(
            "Link inference from observations not yet implemented — waiting for schema extension"
        )

    def to_pyg_data(self) -> Any:  # Use Any to avoid import-time dependency
        """Export current graph to PyTorch Geometric Data object (Assistant only).

        Returns:
            torch_geometric.data.Data object (or raises if called on edge)
        """
        if check_device.is_edge_device:
            raise RuntimeError(
                "to_pyg_data() is not supported on edge Appliance (requires PyTorch)"
            )

        if torch is None or Data is None:
            raise ImportError("torch and torch_geometric are required for PyG export")

        if not self.graph.nodes:
            return Data(
                x=torch.empty((0, 0)), edge_index=torch.empty((2, 0), dtype=torch.long)
            )

        # Node features: collect all numeric attributes in consistent order
        node_attrs = []
        attr_names = None
        for _, data in self.graph.nodes(data=True):
            numeric = {k: v for k, v in data.items() if isinstance(v, (int, float))}
            if attr_names is None:
                attr_names = sorted(numeric.keys())
            values = [numeric.get(k, 0.0) for k in attr_names]
            node_attrs.append(values)

        x = torch.tensor(node_attrs, dtype=torch.float)

        # Edge index (undirected → both directions already in graph)
        edge_index_list = []
        edge_attr_list = []
        for u, v, edata in self.graph.edges(data=True):
            edge_index_list.append([u, v])
            numeric_edge = {
                k: v for k, v in edata.items() if isinstance(v, (int, float))
            }
            edge_values = [numeric_edge.get(k, 0.0) for k in sorted(numeric_edge)]
            edge_attr_list.append(edge_values if edge_values else [0.0])

        edge_index = torch.tensor(edge_index_list, dtype=torch.long).t().contiguous()
        edge_attr = (
            torch.tensor(edge_attr_list, dtype=torch.float) if edge_attr_list else None
        )

        return Data(x=x, edge_index=edge_index, edge_attr=edge_attr)


def build_topology_from_observations(
    observations: List[RLObservation],
    known_links: List[Tuple[str, str]] | None = None,
    device_info: Dict[str, Dict[str, Any]] | None = None,
) -> TopologyGraphBuilder:
    """Convenience factory to build graph from observation batch.

    Args:
        observations: List of RLObservation from different devices
        known_links: Optional explicit (source_id, target_id) pairs
        device_info: Optional device metadata for type/features

    Returns:
        Filled TopologyGraphBuilder instance
    """
    builder = TopologyGraphBuilder()
    device_info = device_info or {}

    builder.from_observation_batch(
        observations=observations,
        device_info=device_info,
        infer_links=True,
    )

    if known_links:
        for src, tgt in known_links:
            builder.add_link(src, tgt)

    return builder
