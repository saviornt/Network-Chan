"""SQLAlchemy 2.0 declarative table definitions for Network-Chan SQLite database.

These models define the actual database schema and should stay in sync with
the Pydantic validation models in database_schema_models.py.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    Integer,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    # Automatically set created/updated timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Incident(Base):
    """Table storing detected network incidents/anomalies."""

    __tablename__ = "incidents"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        index=True,
    )
    incident_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    device_mac: Mapped[Optional[str]] = mapped_column(
        String(17),
        nullable=True,
        index=True,
    )
    device_ip: Mapped[Optional[str]] = mapped_column(
        String(45),  # IPv6 support
        nullable=True,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="warning",
    )
    extra_metadata: Mapped[dict] = mapped_column(
        # JSONB would be better in PostgreSQL, but we use JSON for SQLite
        # In SQLite this becomes TEXT internally
        "JSON",
        nullable=False,
        default=dict,
    )
    timestamp_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    timestamp_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    resolved: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    resolution_action: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    affected_devices: Mapped[list[str]] = mapped_column(
        "JSON",
        nullable=False,
        default=list,
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_incidents_timestamp_start", "timestamp_start"),
        Index("ix_incidents_device_mac", "device_mac"),
        Index("ix_incidents_incident_type", "incident_type"),
        Index("ix_incidents_resolved", "resolved"),
    )

    def __repr__(self) -> str:
        return f"<Incident id={self.id} type={self.incident_type} severity={self.severity}>"


class ModelRegistry(Base):
    """Table tracking versions of trained ML models."""

    __tablename__ = "model_registry"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        index=True,
    )
    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    model_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    trained_on: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    model_hash: Mapped[str] = mapped_column(
        String(64),  # sha256 hex
        nullable=False,
        unique=True,
        index=True,
    )
    file_path: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
    )
    performance_metrics: Mapped[dict] = mapped_column(
        "JSON",
        nullable=False,
        default=dict,
    )

    __table_args__ = (
        Index(
            "ix_model_registry_model_name_version", "model_name", "version", unique=True
        ),
    )

    def __repr__(self) -> str:
        return f"<ModelRegistry {self.model_name} v{self.version}>"


class PolicyAudit(Base):
    """Audit log for all automated or approved policy actions."""

    __tablename__ = "policy_audits"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        index=True,
    )
    incident_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("incidents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action_taken: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    executed_by: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    approved_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    # Relationship (optional, for easier querying if needed later)
    incident: Mapped[Optional["Incident"]] = relationship(
        "Incident", back_populates="policy_audits", uselist=False
    )

    __table_args__ = (
        Index("ix_policy_audits_incident_id", "incident_id"),
        Index("ix_policy_audits_timestamp", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<PolicyAudit id={self.id} action={self.action_taken} success={self.success}>"


class User(Base):
    """Table for persistent user accounts with role-based access control and TOTP support."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        index=True,
        doc="Unique UUID primary key for the user",
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique username for login",
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
        doc="Optional email address for recovery / notifications",
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Argon2 hashed password (never plaintext)",
    )
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="viewer",
        doc="RBAC role: viewer, operator, admin",
    )
    totp_secret: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Encrypted base32 TOTP secret (if 2FA enabled)",
    )
    totp_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether TOTP two-factor authentication is active",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        doc="Account status - false = disabled/locked",
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of most recent successful login",
    )

    __table_args__ = (
        Index("ix_users_username", "username", unique=True),
        Index("ix_users_email", "email", unique=True),
        Index("ix_users_role", "role"),
    )

    def __repr__(self) -> str:
        return (
            f"<User username={self.username} role={self.role} active={self.is_active}>"
        )


class FaissVectorMetadata(Base):
    """Table linking FAISS internal vector IDs to Network-Chan entities (incidents, models, etc.).

    Used for hybrid vector + metadata retrieval in RAG flows.
    """

    __tablename__ = "faiss_vectors_metadata"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        index=True,
        doc="Primary key of the metadata record",
    )

    vector_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        unique=True,
        doc="FAISS-internal vector ID (assigned when vector is added to index)",
    )

    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Type of linked entity: 'incident', 'model_version', 'policy_audit', etc.",
    )

    entity_id: Mapped[UUID] = mapped_column(
        String(36),  # UUID as string for easier querying without joins
        nullable=False,
        index=True,
        doc="Foreign key / reference to the linked entity (e.g. incidents.id)",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Human-readable summary of the vector content",
    )

    embedding_model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Name/version of the embedding model used (e.g. 'all-MiniLM-L6-v2')",
    )

    extra: Mapped[dict] = mapped_column(
        "JSON",
        nullable=False,
        default=dict,
        doc="Flexible additional context (timestamps, device MAC, etc.)",
    )

    # Standard audit fields (inherited from Base)
    # created_at, updated_at already present via Base

    __table_args__ = (
        Index("ix_faiss_vectors_metadata_vector_id", "vector_id", unique=True),
        Index(
            "ix_faiss_vectors_metadata_entity_type_entity_id",
            "entity_type",
            "entity_id",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<FaissVectorMetadata vector_id={self.vector_id} "
            f"entity_type={self.entity_type} entity_id={self.entity_id}>"
        )
