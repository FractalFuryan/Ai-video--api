"""Ethics module - ethical constraints and validation."""
from .constraints import (
    GeometryEthicsGuard,
    validate_geometry,
    safe_validate_geometry,
    FORBIDDEN_KINDS,
    FORBIDDEN_PARAMS
)

__all__ = [
    "GeometryEthicsGuard",
    "validate_geometry", 
    "safe_validate_geometry",
    "FORBIDDEN_KINDS",
    "FORBIDDEN_PARAMS"
]
