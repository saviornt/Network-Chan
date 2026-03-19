"""FAISS-specific configuration settings for Network-Chan.

Uses Pydantic Settings (v2) for type-safe, environment-aware configuration.
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class FaissSettings(BaseSettings):
    """Configuration for the FAISS vector index used in RAG/retrieval."""

    # Index file location
    index_name: str = Field(
        default="network_chan_vectors.index",
        description="Filename of the FAISS index file (without path)",
    )

    index_dir: Path = Field(
        default=Path.home() / ".network-chan" / "data" / "faiss",
        description="Base directory where the FAISS index is stored",
    )

    # Computed full path (read-only property)
    @property
    def full_index_path(self) -> Path:
        """Full absolute path to the FAISS index file."""
        return self.index_dir / self.index_name

    # Vector dimensionality (must match embedding model)
    dimension: int = Field(
        default=384,  # common for sentence-transformers/all-MiniLM-L6-v2
        ge=64,
        le=4096,
        description="Dimensionality of the vectors stored in the index",
    )

    # Index type / hyperparameters
    """
    Only switch to IVFFlat (or better: HNSW + PQ) when you hit one of these triggers:

    Measured search latency > 50–100 ms consistently on real hardware
    Vector count > 100k and growing
    You add quantization/compression needs (PQ/OPQ)
    You start doing very high-QPS searches (unlikely in homelab)
    """
    index_type: str = Field(
        default="FlatL2",
        description="FAISS index factory type (FlatL2 for MVP, IVFFlat later)",
    )

    # Persistence & performance
    save_on_add: bool = Field(
        default=True,
        description="Automatically save index to disk after every add_vectors call",
    )

    # Logging / debug
    verbose: bool = Field(
        default=False,
        description="Enable verbose FAISS output (useful for debugging)",
    )

    model_config = SettingsConfigDict(
        env_prefix="FAISS_",
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


# Singleton instance
faiss_settings = FaissSettings()
