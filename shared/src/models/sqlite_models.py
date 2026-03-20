"""SQLAlchemy 2.0 declarative table definitions for Network-Chan SQLite database.

These models define the actual database schema and should stay in sync with
the Pydantic validation models in database_schema_models.py.
"""

from datetime import datetime


from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


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
