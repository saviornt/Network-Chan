"""Checkpoint serialization and deserialization for Q-Learning approximators.

This module provides safe, versioned save/load functionality for tabular
Q-tables (and future neural approximators) along with metadata.

Key principles:
- Fail-open: never raise in production paths — log and return fallback values
- Structured logging: all errors/warnings/info go through logging_factory
- Portable format: numpy .npz with compressed Q-table + JSON metadata
- Edge-friendly: minimal dependencies, no torch required for tabular MVP

Format (v1.0):
- .npz file containing:
  - 'q_table': 2D float32 array (flattened if needed)
  - 'metadata_json': UTF-8 encoded JSON of TabularQCheckpointMetadata
  - 'format_version': string '1.0'

All functions are designed for round-trip usage:
edge → save → MQTT/file transfer → central load → train → save → edge load
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple, Union

import numpy as np

from shared.src.models.rl_core_models import TabularQCheckpointMetadata
from shared.src.utils.logging_factory import get_logger

logger = get_logger("q_learning.io.serialization")


def save_tabular_checkpoint(
    q_table: np.ndarray,
    metadata: TabularQCheckpointMetadata,
    filepath: Union[str, Path],
    format_version: str = "1.0",
) -> bool:
    """Save a tabular Q-table and metadata to a compressed .npz file.

    Logs success or any write issues but does not raise.

    Args:
        q_table: 2D numpy array of shape (n_states, n_actions), float32
        metadata: Validated metadata model
        filepath: Destination path (will append .npz if missing)
        format_version: Checkpoint format identifier

    Returns:
        True if saved successfully, False if failed (logged)
    """
    filepath = Path(filepath)
    if filepath.suffix.lower() != ".npz":
        filepath = filepath.with_suffix(".npz")

    try:
        if q_table.ndim != 2 or q_table.dtype != np.float32:
            logger.error(
                "Invalid Q-table shape or dtype for saving",
                shape=q_table.shape,
                dtype=str(q_table.dtype),
                expected="2D float32",
                filepath=str(filepath),
            )
            return False

        # Prepare data
        metadata_dict = metadata.model_dump(mode="json")
        save_dict = {
            "q_table": q_table,
            "metadata_json": json.dumps(metadata_dict).encode("utf-8"),
            "format_version": format_version,
        }

        np.savez_compressed(filepath, **save_dict)
        logger.info(
            "Tabular checkpoint saved successfully",
            filepath=str(filepath),
            n_states=q_table.shape[0],
            n_actions=q_table.shape[1],
            episode_count=metadata.episode_count,
            format_version=format_version,
        )
        return True

    except Exception as e:
        logger.exception(
            "Failed to save tabular checkpoint",
            error_type=type(e).__name__,
            error_msg=str(e),
            filepath=str(filepath),
            operation="save_tabular_checkpoint",
        )
        return False


def load_tabular_checkpoint(
    filepath: Union[str, Path],
    fallback_n_states: int = 256,
    fallback_n_actions: int = 4,
) -> Tuple[np.ndarray, TabularQCheckpointMetadata]:
    """Load a tabular Q-table checkpoint and metadata.

    If loading fails (missing file, corrupt, wrong format), logs the issue
    and returns a zero-initialized fallback Q-table + minimal metadata.

    Args:
        filepath: Path to the .npz checkpoint file
        fallback_n_states: Default states for fallback Q-table
        fallback_n_actions: Default actions for fallback Q-table

    Returns:
        Tuple of (q_table: np.ndarray, metadata: TabularQCheckpointMetadata)
    """
    filepath = Path(filepath)
    operation_ctx = {"operation": "load_checkpoint", "filepath": str(filepath)}

    try:
        if not filepath.exists():
            logger.warning(
                "Checkpoint file not found - using fallback",
                **operation_ctx,
                action="returning_fallback",
            )
            return _create_fallback_q(fallback_n_states, fallback_n_actions)

        with np.load(filepath, allow_pickle=False) as data:
            if "q_table" not in data or "metadata_json" not in data:
                logger.error(
                    "Checkpoint missing required keys",
                    keys=list(data.keys()),
                    **operation_ctx,
                )
                return _create_fallback_q(fallback_n_states, fallback_n_actions)

            q_table = data["q_table"]
            if q_table.ndim != 2 or q_table.dtype != np.float32:
                logger.error(
                    "Loaded Q-table has invalid shape or dtype",
                    shape=q_table.shape,
                    dtype=str(q_table.dtype),
                    **operation_ctx,
                )
                return _create_fallback_q(fallback_n_states, fallback_n_actions)

            metadata_bytes = data["metadata_json"].tobytes()
            try:
                metadata_dict = json.loads(metadata_bytes.decode("utf-8"))
                metadata = TabularQCheckpointMetadata.model_validate(metadata_dict)
            except Exception as e:
                logger.error(
                    "Failed to parse checkpoint metadata JSON",
                    error_type=type(e).__name__,
                    error_msg=str(e),
                    **operation_ctx,
                )
                return _create_fallback_q(
                    fallback_n_states, fallback_n_actions, reason="corrupt_metadata"
                )

            logger.info(
                "Tabular checkpoint loaded successfully",
                n_states=q_table.shape[0],
                n_actions=q_table.shape[1],
                episode_count=metadata.episode_count,
                source=metadata.source,
                **operation_ctx,
            )
            return q_table, metadata

    except Exception as e:
        logger.exception(
            "Unexpected error loading checkpoint - using fallback",
            error_type=type(e).__name__,
            error_msg=str(e),
            **operation_ctx,
        )
        return _create_fallback_q(fallback_n_states, fallback_n_actions)


def _create_fallback_q(
    n_states: int, n_actions: int, reason: str = "unknown"
) -> Tuple[np.ndarray, TabularQCheckpointMetadata]:
    """Internal helper: create zero-initialized fallback Q-table and metadata."""
    fallback_q = np.zeros((n_states, n_actions), dtype=np.float32)
    fallback_meta = TabularQCheckpointMetadata(
        created_at=datetime.now(timezone.utc),
        episode_count=0,
        total_steps=0,
        avg_reward_last_100=0.0,
        epsilon=1.0,
        source="edge",
        fallback_reason=reason,
    )
    return fallback_q, fallback_meta


def get_checkpoint_info(filepath: Union[str, Path]) -> Dict[str, Any]:
    """Quickly inspect metadata without loading the full Q-table.

    Returns empty dict on failure (logged).

    Args:
        filepath: Path to .npz file

    Returns:
        Dict with basic metadata fields or empty on failure
    """
    filepath = Path(filepath)
    ctx = {"operation": "get_checkpoint_info", "filepath": str(filepath)}

    try:
        with np.load(filepath, allow_pickle=False) as data:
            if "metadata_json" not in data:
                logger.warning("No metadata found in checkpoint", **ctx)
                return {}

            metadata_bytes = data["metadata_json"].tobytes()
            metadata_dict = json.loads(metadata_bytes.decode("utf-8"))

        return {
            "created_at": metadata_dict.get("created_at"),
            "source": metadata_dict.get("source"),
            "episode_count": metadata_dict.get("episode_count"),
            "total_steps": metadata_dict.get("total_steps"),
            "avg_reward_last_100": metadata_dict.get("avg_reward_last_100"),
            "epsilon": metadata_dict.get("epsilon"),
            "format_version": metadata_dict.get("version", "unknown"),
        }

    except Exception as e:
        logger.exception(
            "Failed to retrieve checkpoint info",
            error_type=type(e).__name__,
            error_msg=str(e),
            **ctx,
        )
        return {}
