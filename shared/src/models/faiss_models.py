"""Pydantic v2 models related to FAISS vector storage and retrieval."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class VectorMetadataBase(BaseModel):
    """Base metadata fields for every stored vector."""

    entity_type: str = Field(
        ..., description="Type of linked entity (incident, model_version, etc.)"
    )
    entity_id: UUID = Field(..., description="UUID of the linked entity")
    description: Optional[str] = Field(
        None, description="Human-readable summary of what this vector represents"
    )
    created_at: datetime = Field(..., description="When the vector was added")


class VectorMetadataCreate(VectorMetadataBase):
    """Fields required when adding a new vector + metadata."""

    vector_id: int = Field(
        ..., description="FAISS internal vector ID (assigned on add)"
    )
    embedding_model: str = Field(
        ..., description="Name/version of embedding model used"
    )
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Any additional context (e.g. timestamp range, device MAC)",
    )


class VectorMetadataRead(VectorMetadataCreate):
    """Full metadata record as read from SQLite."""

    id: UUID = Field(..., description="Primary key in faiss_vectors_metadata table")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VectorSearchResult(BaseModel):
    """Single result from FAISS similarity search."""

    vector_id: int = Field(..., description="FAISS internal ID")
    distance: float = Field(..., description="L2 distance (lower = more similar)")
    score: float = Field(..., description="Normalized similarity (1 - distance/max)")
    metadata: VectorMetadataRead
