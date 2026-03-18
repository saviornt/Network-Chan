"""Multi-agent coordination utilities for shared RL in Network-Chan.

Provides lightweight mechanisms to combine outputs/rewards from multiple agents
(e.g., access points, routers) during inference or training.

Designed to be fast on edge (Appliance) and extensible for central simulation.
Uses Numba for aggregation hot paths.
"""

from __future__ import annotations

from typing import List

import numba as nb
import numpy as np

from shared.src.models.rl_model import RewardSignal, RLAction


@nb.njit(fastmath=True, cache=True)
def _aggregate_rewards_numba(
    values: np.ndarray,
    method_idx: int,
) -> float:
    """Numba-accelerated reward aggregation.

    method_idx:
        0 = mean
        1 = median
        2 = min (conservative)
        3 = max (optimistic)
        4 = weighted mean (weights must be provided externally)
    """
    if len(values) == 0:
        return 0.0

    if method_idx == 0:  # mean
        return float(np.mean(values))
    elif method_idx == 1:  # median
        return float(np.median(values))
    elif method_idx == 2:  # min
        return float(np.min(values))
    elif method_idx == 3:  # max
        return float(np.max(values))
    else:
        return float(np.mean(values))  # fallback


def aggregate_rewards(
    rewards: List[RewardSignal],
    method: str = "mean",
    weights: List[float] | None = None,
) -> RewardSignal:
    """Aggregate rewards from multiple agents into a single consensus reward.

    Args:
        rewards: List of RewardSignal from different agents.
        method: Aggregation strategy ("mean", "median", "min", "max", "weighted").
        weights: Optional per-agent weights (must sum to 1.0 if provided).

    Returns:
        Consensus RewardSignal (scalar value + averaged components).
    """
    if not rewards:
        return RewardSignal(value=0.0, components={}, timestamp=0.0)

    # Extract scalar values
    values = np.array([r.value for r in rewards], dtype=np.float32)

    # Map method to index for Numba
    method_map = {"mean": 0, "median": 1, "min": 2, "max": 3, "weighted": 4}
    if method not in method_map:
        raise ValueError(f"Unsupported aggregation method: {method}")

    method_idx = method_map[method]

    if method == "weighted":
        if weights is None or len(weights) != len(rewards):
            raise ValueError(
                "Weights must be provided and match reward count for 'weighted'"
            )
        weights_arr = np.array(weights, dtype=np.float32)
        if not np.isclose(np.sum(weights_arr), 1.0, atol=1e-5):
            raise ValueError("Weights must sum to approximately 1.0")
        consensus_value = np.sum(values * weights_arr)
    else:
        consensus_value = _aggregate_rewards_numba(values, method_idx)

    # Average components for explainability
    all_components = [r.components for r in rewards]
    if all_components and all_components[0]:  # if components exist
        keys = all_components[0].keys()
        avg_components = {}
        for key in keys:
            avg_components[key] = np.mean([c.get(key, 0.0) for c in all_components])
    else:
        avg_components = {}

    # Use latest timestamp (or average if needed)
    latest_ts = max(r.timestamp for r in rewards)

    return RewardSignal(
        value=float(consensus_value),
        components=avg_components,
        timestamp=latest_ts,
    )


def consensus_action_selection(
    proposed_actions: List[RLAction],
    method: str = "confidence_weighted",
) -> RLAction | None:
    """Select a single consensus action from multiple agent proposals.

    Args:
        proposed_actions: List of RLAction from different agents.
        method: "confidence_weighted" (default), "majority", "highest_confidence".

    Returns:
        Consensus action or None if no agreement.
    """
    if not proposed_actions:
        return None

    if method == "highest_confidence":
        # Pick action with max confidence
        return max(proposed_actions, key=lambda a: a.confidence)

    elif method == "majority":
        # Simple majority vote by (action_type, value) tuple
        from collections import Counter

        votes = Counter((a.action_type, str(a.value)) for a in proposed_actions)
        most_common = votes.most_common(1)
        if most_common and most_common[0][1] > len(proposed_actions) / 2:
            # Found majority → return first matching action
            winner = most_common[0][0]
            for a in proposed_actions:
                if (a.action_type, str(a.value)) == winner:
                    return a
        return None  # no majority

    elif method == "confidence_weighted":
        # Weighted average if continuous, or weighted vote if discrete
        # For simplicity: pick highest confidence for now (extend later)
        return max(proposed_actions, key=lambda a: a.confidence)

    else:
        raise ValueError(f"Unsupported consensus method: {method}")
