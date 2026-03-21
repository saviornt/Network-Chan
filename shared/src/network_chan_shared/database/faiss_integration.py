"""Higher-level FAISS service integrating vector index + SQLite metadata.

Handles add/search with automatic metadata persistence and retrieval.
"""

import asyncio
from typing import List

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from .crud import (
    create_vector_metadata,
    get_vector_metadata_by_faiss_id,
)
from .faiss import FaissIndex
from ..models.faiss_models import VectorMetadataCreate, VectorSearchResult
from ..utils.logging_factory import get_logger

logger = get_logger(component="database.faiss_integration")


class FaissService:
    """Service combining FAISS vector search with SQLite metadata storage."""

    def __init__(self):
        self.index_wrapper = FaissIndex()

    async def add_vector_with_metadata(
        self,
        db: AsyncSession,
        vector: np.ndarray,
        metadata: VectorMetadataCreate,
    ) -> int:
        """
        Add one vector + its metadata (transactional).

        Args:
            db: Active session
            vector: 1D float32 array of size dimension
            metadata: Validated metadata (entity_type, entity_id, etc.)

        Returns:
            int: FAISS internal vector ID
        """
        if vector.shape != (self.index_wrapper.dimension,):
            raise ValueError(
                f"Expected 1D vector of size {self.index_wrapper.dimension}"
            )

        # Add to FAISS first → get its ID
        faiss_id = self.index_wrapper.add_vectors(vector.reshape(1, -1))[0]

        # Persist metadata linking FAISS ID to entity
        metadata.vector_id = faiss_id
        await create_vector_metadata(db, metadata)

        logger.info(
            "Vector added with metadata",
            faiss_id=faiss_id,
            entity_type=metadata.entity_type,
            entity_id=str(metadata.entity_id),
        )
        return faiss_id

    async def search_with_metadata(
        self,
        db: AsyncSession,
        query_vector: np.ndarray,
        k: int = 5,
    ) -> List[VectorSearchResult]:
        """
        Search FAISS index and enrich results with SQLite metadata.

        Args:
            db: Active session
            query_vector: 1D or 2D float32 query
            k: Number of results

        Returns:
            List[VectorSearchResult]: Enriched results sorted by similarity
        """
        distances, indices = self.index_wrapper.search(query_vector, k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:  # FAISS padding
                continue

            # Fetch metadata from SQLite by FAISS vector_id
            metadata = await get_vector_metadata_by_faiss_id(db, idx)
            if metadata:
                # Simple score normalization (L2 distance → cosine-like)
                score = 1.0 - (dist / (self.index_wrapper.dimension**0.5 * 2))
                results.append(
                    VectorSearchResult(
                        vector_id=idx,
                        distance=float(dist),
                        score=score,
                        metadata=metadata,
                    )
                )

        logger.debug(
            "FAISS hybrid search completed", query_count=1, result_count=len(results)
        )
        return sorted(results, key=lambda x: x.score, reverse=True)


# Global singleton (or inject via FastAPI Depends if preferred)
faiss_service = FaissService()


# Helper to run sync FAISS calls in thread if needed (rare)
def run_in_thread(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return loop.run_in_executor(None, lambda: func(*args, **kwargs))


# Helper to run search time benchmark (for tuning index type/hyperparameters)
def benchmark_search_time(self, n_queries: int = 100, k: int = 10):
    import time

    times = []
    for _ in range(n_queries):
        q = np.random.randn(1, self.dimension).astype(np.float32)
        start = time.perf_counter()
        self.search(q, k)
        times.append(time.perf_counter() - start)
    logger.info(
        "FAISS search benchmark",
        avg_ms=np.mean(times) * 1000,
        p95_ms=np.percentile(times, 95) * 1000,
    )
