"""Base Pydantic model with shared configuration for the entire project."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class NetworkChanBaseModel(BaseModel):
    """Common base class for all validation models in Network-Chan.

    Enforces strict validation, immutability where desired, and consistent JSON
    serialization behavior.
    """

    model_config = ConfigDict(
        extra="forbid",  # reject unknown fields
        frozen=False,  # allow mutation unless subclass overrides
        str_strip_whitespace=True,
        validate_default=True,
        validate_assignment=True,
        arbitrary_types_allowed=False,
        json_schema_extra={"examples": []},  # can be overridden per model
    )
