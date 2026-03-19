"""FAISS vector index configuration for Network-Chan RAG/retrieval.

Uses Pydantic Settings v2 for type-safe loading from .env with FAISS_ prefix.
Singleton: `from shared.src.settings.faiss_settings import faiss_settings`

Handles index location, dimensionality, index type, persistence behavior.
Index directory is auto-created on first access.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.src.utils.logging_factory import get_logger


logger = get_logger("faiss_settings", category="settings")


class FaissSettings(BaseSettings):
    """Configuration for the FAISS vector store (RAG/incident retrieval).

    All paths are resolved relative to index_dir.
    Directory creation happens lazily on first property access.
    """

    model_config = SettingsConfigDict(
        env_prefix="FAISS_",
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
        env_ignore_empty=True,
    )

    index_name: str = Field(
        default="network_chan_vectors.index",
        description="Base filename of the FAISS index file (no extension needed)",
    )

    index_dir: Path = Field(
        default=Path.home() / ".network-chan" / "data" / "faiss",
        description="Directory where FAISS index files are stored",
    )

    dimension: int = Field(
        default=384,  # Matches all-MiniLM-L6-v2 / common small embedders
        ge=64,
        le=4096,
        description="Dimensionality of stored vectors (must match embedding model)",
    )

    index_type: str = Field(
        default="FlatL2",
        description=(
            "FAISS index type/factory string. "
            "Start with 'FlatL2' (exact, MVP). "
            "Later: 'IVFFlat', 'HNSW', 'PQ' for scale."
        ),
    )

    save_on_add: bool = Field(
        default=True,
        description="Auto-save index to disk after every add_vectors operation",
    )

    verbose: bool = Field(
        default=False,
        description="Enable verbose FAISS internal logging (debug only)",
    )

    @model_validator(mode="after")
    def ensure_index_dir_exists(self) -> "FaissSettings":
        """Lazily create the index directory after validation."""
        if not self.index_dir.exists():
            try:
                self.index_dir.mkdir(parents=True, exist_ok=True)
                logger.info(
                    "Created FAISS index directory",
                    path=str(self.index_dir),
                )
            except OSError as exc:
                logger.warning(
                    "Failed to create FAISS index directory — ensure permissions",
                    path=str(self.index_dir),
                    exc_info=exc,
                )
        return self

    @property
    def full_index_path(self) -> Path:
        """Full absolute path to the primary FAISS index file."""
        return self.index_dir / self.index_name

    # TODO: Add future params (when scaling)
    # nprobe: int = Field(default=1, ge=1)               # IVFFlat probe count
    # m: int = Field(default=32, ge=8)                   # HNSW M parameter
    # ef_construction: int = Field(default=200, ge=40)   # HNSW construction param
    # quantization: Literal["none", "pq", "opq"] = "none"


# Singleton instance
faiss_settings: FaissSettings = FaissSettings()


__all__ = ["FaissSettings", "faiss_settings"]
