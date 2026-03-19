"""SQLite-specific configuration settings for Network-Chan.

Uses Pydantic Settings (v2) for type-safe, environment-aware configuration.
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SQLiteSettings(BaseSettings):
    """Configuration for the SQLite database used by both Appliance and Assistant."""

    # Database file location (absolute path preferred)
    db_name: str = Field(
        default="network_chan.db",
        description="Filename of the SQLite database (without path)",
    )

    db_dir: Path = Field(
        default=Path.home() / ".network-chan" / "data" / "sqlite",
        description="Base directory where the database file is stored",
    )

    # Computed full path (read-only property)
    @property
    def full_db_path(self) -> Path:
        """Full absolute path to the SQLite database file."""
        return self.db_dir / self.db_name

    # Connection pool settings (sensible defaults for Raspberry Pi)
    pool_size: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of persistent connections in the pool",
    )

    pool_timeout: float = Field(
        default=30.0,
        ge=5.0,
        description="Timeout in seconds for acquiring a connection from the pool",
    )

    pool_pre_ping: bool = Field(
        default=True,
        description="Enable connection health check before handing out from pool",
    )

    # Debugging / observability
    echo: bool = Field(
        default=False,
        description="If True, SQLAlchemy will log all SQL statements (dev only)",
    )

    # WAL mode is always enabled — no setting needed (hardcoded for safety)

    model_config = SettingsConfigDict(
        env_prefix="SQLITE_",
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


# Singleton instance (preferred way to access settings)
sqlite_settings = SQLiteSettings()

__all__ = [
    "SQLiteSettings",
    "sqlite_settings",
]
