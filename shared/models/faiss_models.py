"""Pydantic v2 schemas and SQLAlchemy ORM model for FAISS vector metadata.

This file defines the persistent link between FAISS internal vector IDs and
Network-Chan business entities (incidents, model versions, policy audits, etc.).
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.sqlite_models import Base


class VectorMetadataBase(BaseModel):
    """Common metadata fields shared across FAISS vector schemas."""

    entity_type: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Type of linked entity (e.g. 'incident', 'model_version')",
    )
    entity_id: UUID = Field(..., description="UUID of the linked entity")
    description: Optional[str] = Field(
        None, max_length=500, description="Human-readable summary of the vector content"
    )
    embedding_model: str = Field(
        ...,
        min_length=5,
        max_length=100,
        description="Name/version of embedding model (e.g. 'all-MiniLM-L6-v2')",
    )
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Flexible additional context (timestamps, device MAC, etc.)",
    )

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "examples": [{"entity_type": "incident", "entity_id": "550e8400-..."}]
        },
    )


class VectorMetadataCreate(VectorMetadataBase):
    """Schema for creating a new vector metadata entry (before/after FAISS add)."""

    # vector_id is assigned by FAISS after index.add() — not required on create
    # Set it in the service layer after insertion
    vector_id: Optional[int] = Field(
        default=None, description="FAISS internal vector ID (set after adding to index)"
    )


class VectorMetadataRead(VectorMetadataCreate):
    """Full metadata record as returned from database queries."""

    id: UUID = Field(..., description="Primary key in faiss_vectors_metadata table")
    created_at: datetime
    updated_at: datetime


class VectorSearchResult(BaseModel):
    """Single result from a FAISS similarity search."""

    vector_id: int = Field(..., description="FAISS internal vector ID")
    distance: float = Field(..., description="Raw L2 distance (lower = more similar)")
    score: float = Field(
        ..., description="Normalized similarity score (higher = better)"
    )
    metadata: VectorMetadataRead = Field(..., description="Full linked metadata")


class FaissVectorMetadata(Base):
    """SQLAlchemy ORM model linking FAISS vector IDs to Network-Chan entities.

    Used for hybrid RAG: vector similarity → metadata lookup → entity retrieval.
    """

    __tablename__ = "faiss_vectors_metadata"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        index=True,
        doc="Primary key of this metadata record",
    )
    vector_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        unique=True,
        index=True,
        doc="FAISS-assigned vector ID (set after index.add())",
    )
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Type of linked entity (incident, model_version, policy_audit, etc.)",
    )
    entity_id: Mapped[UUID] = mapped_column(
        String(36),  # Stored as string for simple querying/indexing
        nullable=False,
        index=True,
        doc="Reference to the linked entity's UUID",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Human-readable summary of what this vector represents",
    )
    embedding_model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Embedding model name/version used to generate the vector",
    )
    extra: Mapped[dict] = mapped_column(
        "JSON",
        nullable=False,
        default=dict,
        doc="Arbitrary additional context (timestamps, device info, etc.)",
    )

    __table_args__ = (
        Index("ix_faiss_vectors_metadata_vector_id", "vector_id", unique=True),
        Index(
            "ix_faiss_vectors_metadata_entity_lookup",
            "entity_type",
            "entity_id",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<FaissVectorMetadata id={self.id} vector_id={self.vector_id} "
            f"entity={self.entity_type}/{self.entity_id}>"
        )


__all__ = [
    "VectorMetadataBase",
    "VectorMetadataCreate",
    "VectorMetadataRead",
    "VectorSearchResult",
    "FaissVectorMetadata",
]
