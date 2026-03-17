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


class MLBaseModel(BaseModel):
    """Base Pydantic model for all ML/RL data structures.

    Enforces strict validation, forbids extra fields, and uses type coercion
    where safe. Designed for edge (Appliance) and central (Assistant) use.
    """

    model_config = ConfigDict(
        strict=True,  # No coercion unless explicit
        extra="forbid",  # No unknown fields
        frozen=False,  # Allow mutation where needed
        validate_assignment=True,  # Validate on attribute set
        populate_by_name=True,  # Allow alias/field name population
        arbitrary_types_allowed=True,  # For NumPy arrays, torch tensors, etc.
    )
