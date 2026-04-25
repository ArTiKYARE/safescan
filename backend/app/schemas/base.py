"""
SafeScan — Base Schema with UUID serialization
"""

from uuid import UUID
from typing import ClassVar
from pydantic import BaseModel, model_validator


class BaseSchema(BaseModel):
    """Base schema that automatically converts UUID fields to strings."""

    UUID_FIELDS: ClassVar[list] = [
        "id", "user_id", "domain_id", "scan_id", "organization_id",
        "vulnerability_id", "resource_id"
    ]

    @model_validator(mode="before")
    @classmethod
    def convert_uuids(cls, values):
        """Convert UUID attributes to strings before validation."""
        if hasattr(values, "__dict__"):
            values = {k: getattr(values, k, None) for k in values.__dict__.keys()
                     if not k.startswith('_')}

        if isinstance(values, dict):
            for field in cls.UUID_FIELDS:
                if field in values and isinstance(values[field], UUID):
                    values[field] = str(values[field])

        return values
