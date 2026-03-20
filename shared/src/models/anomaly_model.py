"""Pydantic schemas, SQLAlchemy ORM record, and FAISS embedding model for anomaly detection results.

This module defines the full lifecycle of an anomaly detection event:
- Pydantic model for validation and transfer
- ORM record for persistent SQLite storage
- Embedding model for FAISS similarity search
"""

from __future__ import annotations

from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Literal, Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from sqlalchemy import Boolean, DateTime, Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.src.models.sqlite_models import (
    Base,
)  # Provides auto created_at / updated_at


class AnomalyDetectionResultModel(BaseModel):
    """Validated output from lightweight anomaly detection (TinyML / threshold-based).

    Used for real-time alerting, incident triggering, and transfer across layers.
    Frozen for immutability.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_default=True,
        validate_assignment=True,
        frozen=True,
    )

    device_id: str = Field(
        ...,
        min_length=1,
        description="Device identifier (MAC, IP, Omada ID, etc.)",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC time when anomaly was detected",
    )
    is_anomaly: bool = Field(
        ...,
        description="True if classified as anomalous",
    )
    anomaly_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Normalized anomaly score (0 = normal, 1 = extreme)",
    )
    severity: Literal["low", "medium", "high", "critical"] = Field(
        default="low",
        description="Human-readable severity level",
    )
    reason: str = Field(
        ...,
        min_length=1,
        description="Short explanation (e.g. 'latency > 200ms for 30s')",
    )
    related_metrics: list[str] = Field(
        default_factory=list,
        description="Metric keys that contributed (e.g. 'latency', 'packet_loss')",
    )

    @field_validator("related_metrics", mode="before")
    @classmethod
    def normalize_metrics(cls, v: Any) -> list[str]:
        """Ensure related_metrics is always a list of strings."""
        if isinstance(v, str):
            return [v.strip()]
        if isinstance(v, list):
            return [str(item).strip() for item in v if item]
        return []


class AnomalyDetectionResultRecord(Base):
    """Persistent SQLite storage for anomaly detection results.

    Stores the full detection event for historical analysis, incident correlation,
    and FAISS embedding generation.
    """

    __tablename__ = "anomaly_detection_results"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        index=True,
        doc="Unique UUID for this anomaly detection record",
    )
    device_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Device identifier (MAC, IP, Omada ID, etc.)",
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="UTC detection timestamp",
    )
    is_anomaly: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        doc="True if classified as anomalous",
    )
    anomaly_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Normalized anomaly score [0.0–1.0]",
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="low",
        doc="Severity level: low, medium, high, critical",
    )
    reason: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Short explanation of detection reason",
    )
    related_metrics: Mapped[list[str]] = mapped_column(
        "JSON",
        nullable=False,
        default=list,
        doc="List of contributing metric names",
    )

    __table_args__ = (
        Index("ix_anomaly_detection_results_timestamp", "timestamp"),
        Index("ix_anomaly_detection_results_device_id", "device_id"),
        Index("ix_anomaly_detection_results_is_anomaly", "is_anomaly"),
        Index("ix_anomaly_detection_results_severity", "severity"),
    )

    def __repr__(self) -> str:
        return (
            f"<AnomalyDetectionResultRecord id={self.id} device={self.device_id} "
            f"anomaly={self.is_anomaly} score={self.anomaly_score}>"
        )


class AnomalyDetectionResultEmbedding(BaseModel):
    """FAISS-ready embedding representation for anomaly detection results.

    This is a lightweight wrapper that holds the vector + key metadata.
    Actual vector storage happens in the FAISS index file; this is used
    during indexing and retrieval.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    vector: list[float] = Field(
        ...,
        description="High-dimensional embedding vector (e.g. 384-dim from MiniLM)",
    )
    anomaly_score: float = Field(..., ge=0.0, le=1.0)
    severity: Literal["low", "medium", "high", "critical"]
    device_id: str
    timestamp: datetime
    description: Optional[str] = Field(default=None, max_length=500)


__all__ = [
    "AnomalyDetectionResultModel",
    "AnomalyDetectionResultRecord",
    "AnomalyDetectionResultEmbedding",
]
