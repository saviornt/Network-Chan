"""Numba-accelerated reward calculation utilities for reinforcement learning.

These functions compute scalar or component-wise rewards from network observations.
They are designed to be extremely fast on edge devices (Raspberry Pi 5 Appliance)
using Numba's njit compilation.

All functions accept or return models from shared.models.rl (e.g. RLObservation → RewardSignal).
"""

from __future__ import annotations

from typing import Dict, List

import numba as nb
import numpy as np
from models.rl import RewardSignal, RLObservation


@nb.njit(fastmath=True, cache=True)
def _compute_reward_components(
    latency_ms: float,
    packet_loss: float,
    client_density: int,
    wifi_noise_floor: float,
    bandwidth_util: float,
) -> tuple[float, float, float, float, float]:  # ← Use built-in tuple here
    """Low-level component penalties (njit inner function).

    Each component is normalized to [0, 1] where 0 = ideal, 1 = very bad.
    Returns tuple: (latency_penalty, loss_penalty, density_penalty, noise_penalty, util_penalty)
    """
    # Latency: linear up to 100 ms, then saturated
    latency_penalty = min(latency_ms / 100.0, 1.0)

    # Packet loss: already [0,1], but amplify small losses
    loss_penalty = packet_loss**1.5  # convex -> penalizes small losses more

    # Client density: linear up to 50 clients, then saturated
    density_penalty = min(client_density / 50.0, 1.0)

    # WiFi noise floor: lower (more negative) is better; normalize -40 to -100 dBm
    noise_norm = max(
        (wifi_noise_floor + 100.0) / 60.0, 0.0
    )  # -40 → ~1.0 bad, -100 → 0 good
    noise_penalty = noise_norm

    # Bandwidth utilization: linear up to 90%, then steep penalty
    util_penalty = min(bandwidth_util / 0.9, 1.0) ** 2  # quadratic after 90%

    return latency_penalty, loss_penalty, density_penalty, noise_penalty, util_penalty


@nb.njit(fastmath=True, cache=True)
def _weighted_reward(
    components: tuple[float, float, float, float, float],  # ← built-in tuple
    weights: tuple[float, float, float, float, float],
) -> float:
    """Compute final scalar reward from weighted components."""
    total_penalty = 0.0
    # Use regular range instead of prange (prange is for parallel, but here loop is tiny → no gain)
    for i in range(5):  # ← change to range → fixes prange not iterable
        total_penalty += components[i] * weights[i]
    return max(1.0 - total_penalty, -1.0)  # bound reward to [-1, 1]


def compute_reward_from_observation(
    obs: RLObservation,
    weights: Dict[str, float] | None = None,
) -> RewardSignal:
    """Calculate reward from a full RLObservation using Numba acceleration.

    Extracts relevant features from the observation vector (assumes fixed order).
    Produces a RewardSignal with scalar value + component breakdown.

    Assumed feature order in obs.features (0-based indices):
        0: latency_mean_ms
        1: packet_loss_rate
        2: client_density
        3: wifi_noise_floor_dbm
        4: bandwidth_utilization

    Args:
        obs: Validated RLObservation instance.
        weights: Optional dict overriding default component weights.

    Returns:
        RewardSignal with value and components dict.
    """
    if len(obs.features) < 5:
        raise ValueError(
            "Observation features must contain at least 5 values for reward calc"
        )

    # Default weights (sum ≈ 1.0)
    default_weights = {
        "latency": 0.30,
        "loss": 0.35,
        "density": 0.15,
        "noise": 0.10,
        "util": 0.10,
    }
    w = default_weights.copy()
    if weights:
        w.update(weights)

    # Extract scalars
    latency_ms = obs.features[0]
    packet_loss = obs.features[1]
    client_density = int(round(obs.features[2]))  # usually integer count
    wifi_noise = obs.features[3]
    bandwidth_util = obs.features[4]

    # Numba-accelerated computation
    components_tuple = _compute_reward_components(
        latency_ms,
        packet_loss,
        client_density,
        wifi_noise,
        bandwidth_util,
    )

    # Weighted scalar reward
    scalar_reward = _weighted_reward(
        components_tuple,
        (w["latency"], w["loss"], w["density"], w["noise"], w["util"]),
    )

    # Build breakdown for explainability
    components_dict = {
        "latency_penalty": components_tuple[0],
        "loss_penalty": components_tuple[1],
        "density_penalty": components_tuple[2],
        "noise_penalty": components_tuple[3],
        "util_penalty": components_tuple[4],
    }

    return RewardSignal(
        value=scalar_reward,
        components=components_dict,
        timestamp=obs.timestamp,
    )


def aggregate_multi_agent_rewards(
    rewards: List[RewardSignal],
    method: str = "mean",
) -> float:
    """Aggregate rewards from multiple agents (e.g. multi-AP coordination).

    Args:
        rewards: List of RewardSignal from different agents.
        method: "mean" (default), "median", "min" (conservative), "max" (optimistic).

    Returns:
        Aggregated scalar reward.
    """
    if not rewards:
        return 0.0

    values = np.array([r.value for r in rewards], dtype=np.float32)

    if method == "mean":
        return float(np.mean(values))
    elif method == "median":
        return float(np.median(values))
    elif method == "min":
        return float(np.min(values))
    elif method == "max":
        return float(np.max(values))
    else:
        raise ValueError(f"Unknown aggregation method: {method}")
