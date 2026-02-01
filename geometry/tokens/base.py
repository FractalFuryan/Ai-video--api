"""
Geometry tokens - structural representations without identity.
"""
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any
from enum import Enum
import numpy as np

class TokenType(Enum):
    """Types of geometry tokens."""
    PRIMITIVE = "primitive"
    TRANSFORM = "transform"
    RELATION = "relation"
    COMPOSITION = "composition"
    TEMPORAL = "temporal"

@dataclass
class GeometryToken:
    """Base geometry token."""
    token_type: TokenType
    parameters: Dict[str, Any]
    bounds: Tuple[float, float, float, float]  # x1, y1, x2, y2
    ethical_constraints: List[str] = None
    
    def to_vector(self) -> np.ndarray:
        """Convert token to vector representation."""
        raise NotImplementedError

@dataclass
class PrimitiveToken(GeometryToken):
    """Geometric primitives."""
    primitive_type: str  # "sphere", "cube", "cylinder", "plane"
    dimensions: Tuple[float, ...]
    material: Dict[str, float] = None  # Reflectivity, transparency, etc.

@dataclass  
class TransformToken(GeometryToken):
    """Transformations."""
    transform_type: str  # "translate", "rotate", "scale", "shear"
    matrix: np.ndarray
    reference_id: str = None  # Token being transformed

@dataclass
class TemporalToken(GeometryToken):
    """Temporal/sequence tokens for video."""
    start_frame: int
    end_frame: int
    interpolation: str  # "linear", "ease_in_out", "bounce"
    keyframes: List[Dict[str, Any]]
