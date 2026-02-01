"""
Geometry Token Specification - The immutable foundation.

Identity-free, structure-only geometry tokens. No pixels, no mesh, no texture.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Tuple, List, Any, Optional
import json
import hashlib


class GeometryTokenType(Enum):
    """Core geometry token types. Extend carefully."""
    PRIMITIVE = "primitive"      # Basic shapes
    TRANSFORM = "transform"      # Spatial transformations
    RELATION = "relation"        # Spatial relationships
    TEMPORAL = "temporal"       # Time-based transformations
    COMPOSITION = "composition" # Groupings/assemblies


@dataclass(frozen=True, eq=True)
class GeometryToken:
    """
    Atomic, identity-free geometry token.
    This is NOT render-specific. This is structure-only.
    
    RULES:
    1. No strings describing anatomy or identity
    2. No ratios matching biometric templates
    3. No pixel, mesh, or texture data
    4. Only numeric geometry & transforms
    5. Immutable once created
    """
    token_type: GeometryTokenType
    kind: str                    # e.g. "cube", "sphere", "rotate_x"
    params: Dict[str, float]     # Numeric only, no strings
    bounds: Tuple[float, float, float] = (1.0, 1.0, 1.0)  # x,y,z extents
    version: int = 1
    uid: Optional[str] = None    # Optional unique ID for references
    
    def __post_init__(self):
        """Validate invariants on creation."""
        # Validate parameter types
        for key, value in self.params.items():
            if not isinstance(value, (int, float)):
                raise TypeError(f"Parameter '{key}' must be numeric, got {type(value)}")
        
        # Generate UID if not provided
        if self.uid is None:
            object.__setattr__(self, 'uid', self._generate_uid())
    
    def _generate_uid(self) -> str:
        """Generate deterministic UID from token content."""
        data = {
            "type": self.token_type.value,
            "kind": self.kind,
            "params": tuple(sorted(self.params.items())),
            "bounds": self.bounds,
            "version": self.version
        }
        json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return f"g{hashlib.sha256(json_str.encode()).hexdigest()[:16]}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dict."""
        return {
            "token_type": self.token_type.value,
            "kind": self.kind,
            "params": self.params,
            "bounds": self.bounds,
            "version": self.version,
            "uid": self.uid
        }
    
    def to_vector(self) -> List[float]:
        """Convert to numeric vector for processing."""
        vector = []
        
        # Token type encoding
        type_map = {t: i/len(GeometryTokenType) for i, t in enumerate(GeometryTokenType)}
        vector.append(type_map[self.token_type])
        
        # Kind (hashed to float)
        kind_hash = int(hashlib.sha256(self.kind.encode()).hexdigest()[:8], 16)
        vector.append((kind_hash % 10000) / 10000)
        
        # Parameters (sorted for determinism)
        for key in sorted(self.params.keys()):
            vector.append(self.params[key])
        
        # Bounds
        vector.extend(self.bounds)
        
        return vector
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GeometryToken':
        """Create token from dict."""
        return cls(
            token_type=GeometryTokenType(data["token_type"]),
            kind=data["kind"],
            params=data["params"],
            bounds=tuple(data["bounds"]),
            version=data.get("version", 1),
            uid=data.get("uid")
        )


# Canonical geometry kinds
PRIMITIVE_KINDS = {
    "cube": {"size": 1.0},
    "sphere": {"radius": 1.0},
    "cylinder": {"radius": 0.5, "height": 1.0},
    "cone": {"radius": 0.5, "height": 1.0},
    "torus": {"major_radius": 1.0, "minor_radius": 0.3},
    "plane": {"width": 1.0, "height": 1.0},
}

TRANSFORM_KINDS = {
    "translate": {"x": 0.0, "y": 0.0, "z": 0.0},
    "rotate_x": {"angle": 0.0},
    "rotate_y": {"angle": 0.0},
    "rotate_z": {"angle": 0.0},
    "scale": {"x": 1.0, "y": 1.0, "z": 1.0},
    "uniform_scale": {"factor": 1.0},
}

RELATION_KINDS = {
    "parent": {"child_uid": ""},
    "group": {"member_uids": []},
    "align": {"target_uid": "", "axis": 0.0},
}

TEMPORAL_KINDS = {
    "oscillate": {"frequency": 1.0, "amplitude": 1.0},
    "rotate_over_time": {"speed": 1.0},
    "pulse": {"period": 2.0, "intensity": 1.0},
}


def create_primitive(kind: str, **kwargs) -> GeometryToken:
    """Create a primitive geometry token with validated parameters."""
    if kind not in PRIMITIVE_KINDS:
        raise ValueError(f"Unknown primitive kind: {kind}. Must be one of: {list(PRIMITIVE_KINDS.keys())}")
    
    # Merge defaults with provided params
    params = PRIMITIVE_KINDS[kind].copy()
    params.update({k: float(v) for k, v in kwargs.items()})
    
    return GeometryToken(
        token_type=GeometryTokenType.PRIMITIVE,
        kind=kind,
        params=params,
        bounds=_calculate_bounds(kind, params)
    )


def _calculate_bounds(kind: str, params: Dict[str, float]) -> Tuple[float, float, float]:
    """Calculate bounding box for primitive."""
    if kind == "cube":
        size = params.get("size", 1.0)
        return (size, size, size)
    elif kind == "sphere":
        radius = params.get("radius", 1.0)
        diameter = radius * 2
        return (diameter, diameter, diameter)
    elif kind == "cylinder" or kind == "cone":
        radius = params.get("radius", 0.5)
        height = params.get("height", 1.0)
        diameter = radius * 2
        return (diameter, height, diameter)
    elif kind == "torus":
        major = params.get("major_radius", 1.0)
        minor = params.get("minor_radius", 0.3)
        size = (major + minor) * 2
        return (size, minor * 2, size)
    elif kind == "plane":
        width = params.get("width", 1.0)
        height = params.get("height", 1.0)
        return (width, height, 0.001)
    
    return (1.0, 1.0, 1.0)
