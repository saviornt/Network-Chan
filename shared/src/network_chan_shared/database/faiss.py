"""Low-level FAISS index wrapper for Network-Chan.

Handles index creation, add/search, persistence, and basic health checks.
Uses FlatL2 for MVP; designed to swap to IVFFlat/quantized later.
"""

import logging
from typing import List, Optional, Tuple, cast

import faiss
import numpy as np

from shared.settings.faiss_settings import faiss_settings
from shared.utils.logging_factory import get_logger

logger = get_logger(
    component="database.faiss", index_path=str(faiss_settings.full_index_path)
)


class FaissIndex:
    """Thread-safe wrapper around a FAISS index with persistence."""

    def __init__(self):
        self.index: Optional[faiss.Index] = None
        self.dimension: int = faiss_settings.dimension
        self._load_or_create()

    def _load_or_create(self) -> None:
        """Load existing index or create a new FlatL2 index."""
        path = faiss_settings.full_index_path
        if path.exists():
            logger.info("Loading existing FAISS index", path=str(path))
            self.index = faiss.read_index(str(path))
            if self.index is None:
                raise RuntimeError("Failed to load FAISS index from disk")
            if self.index.d != self.dimension:
                raise ValueError(
                    f"Loaded index dimension {self.index.d} != configured {self.dimension}"
                )
        else:
            logger.info("Creating new FlatL2 FAISS index", dimension=self.dimension)
            self.index = faiss.IndexFlatL2(self.dimension)
            path.parent.mkdir(parents=True, exist_ok=True)

        # Runtime assertion for type checker
        assert self.index is not None, "Index must be initialized"

    def add_vectors(
        self,
        vectors: np.ndarray,
        ids: Optional[List[int]] = None,
    ) -> List[int]:
        """
        Add vectors to the index and return their assigned IDs.

        Args:
            vectors: shape (n_vectors, dimension) float32 array
            ids: Optional pre-assigned IDs (rarely used)

        Returns:
            List[int]: FAISS-internal IDs assigned to the added vectors
        """
        if self.index is None:
            raise RuntimeError("FAISS index not initialized")

        if vectors.shape[1] != self.dimension:
            raise ValueError(
                f"Vector dim {vectors.shape[1]} != index dim {self.dimension}"
            )

        vectors = vectors.astype(np.float32)  # Ensure correct dtype

        if faiss_settings.verbose:
            faiss.logger.setLevel(logging.DEBUG)

        n_before = self.index.ntotal

        vectors = vectors.astype(np.float32)  # Ensure correct dtype

        # Explicit cast + named args to help type checker
        index_cast = cast(faiss.IndexFlatL2, self.index)

        if ids is None:
            index_cast.add(x=vectors)  # type: ignore[call-arg]
        else:
            xids = np.array(ids, dtype=np.int64)
            index_cast.add_with_ids(x=vectors, xids=xids)  # type: ignore[call-arg]

        assigned_ids = list(range(n_before, self.index.ntotal))
        logger.info(
            "Added vectors to FAISS", count=len(assigned_ids), total=self.index.ntotal
        )

        if faiss_settings.save_on_add:
            self.save()

        return assigned_ids

    def search(
        self,
        query_vector: np.ndarray,
        k: int = 5,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Search for k nearest neighbors.

        Args:
            query_vector: shape (1, dimension) or (dimension,) float32
            k: Number of nearest neighbors

        Returns:
            distances: shape (1, k)
            indices: shape (1, k) — FAISS internal IDs
        """
        if self.index is None:
            raise RuntimeError("FAISS index not initialized")

        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)

        if query_vector.shape[1] != self.dimension:
            raise ValueError(f"Query dim {query_vector.shape[1]} != {self.dimension}")

        query_vector = query_vector.astype(np.float32)

        # Explicit k parameter + cast to help type checker
        distances, indices = self.index.search(x=query_vector, k=k)  # type: ignore[call-arg]

        return distances, indices

    def save(self) -> None:
        """Persist index to disk."""
        if self.index is None:
            raise RuntimeError("Cannot save uninitialized index")

        path = faiss_settings.full_index_path
        faiss.write_index(self.index, str(path))
        logger.info("FAISS index saved", path=str(path))

    def get_total(self) -> int:
        """Current number of vectors in index."""
        if self.index is None:
            return 0
        return self.index.ntotal

    def health_check(self) -> bool:
        """Basic sanity check."""
        return (
            self.index is not None
            and self.index.d == self.dimension
            and self.index.ntotal >= 0
        )
