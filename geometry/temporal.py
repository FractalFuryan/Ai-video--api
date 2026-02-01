"""
Temporal Geometry System - Time-based transformations without pixels.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json
import hashlib
from datetime import datetime
from geometry.spec import GeometryToken, GeometryTokenType


class TemporalInterpolation(Enum):
    """Interpolation methods for temporal transformations."""
    LINEAR = "linear"
    EASE_IN_OUT = "ease_in_out"
    BOUNCE = "bounce"
    SPRING = "spring"
    STEP = "step"


@dataclass(frozen=True)
class TemporalKeyframe:
    """Keyframe in a temporal sequence."""
    frame: int
    value: float
    interpolation: TemporalInterpolation = TemporalInterpolation.LINEAR
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame": self.frame,
            "value": self.value,
            "interpolation": self.interpolation.value
        }


@dataclass(frozen=True)
class TemporalSequence:
    """Complete temporal sequence for a property."""
    target_uid: str  # UID of the geometry token being animated
    property_name: str  # e.g., "rotate_y.angle", "translate.x"
    keyframes: List[TemporalKeyframe]
    duration_frames: int
    
    @property
    def fps(self) -> float:
        """Calculate implied FPS (for 1-second duration reference)."""
        return self.duration_frames
    
    def get_value_at_frame(self, frame: int) -> float:
        """Get interpolated value at specific frame."""
        if not self.keyframes:
            return 0.0
        
        # Clamp frame
        frame = max(0, min(frame, self.duration_frames - 1))
        
        # Find surrounding keyframes
        prev_kf = None
        next_kf = None
        
        for kf in self.keyframes:
            if kf.frame <= frame:
                prev_kf = kf
            if kf.frame >= frame:
                next_kf = kf
                break
        
        if prev_kf is None:
            return self.keyframes[0].value
        if next_kf is None:
            return self.keyframes[-1].value
        if prev_kf.frame == next_kf.frame:
            return prev_kf.value
        
        # Interpolate
        t = (frame - prev_kf.frame) / (next_kf.frame - prev_kf.frame)
        
        if prev_kf.interpolation == TemporalInterpolation.LINEAR:
            return prev_kf.value + (next_kf.value - prev_kf.value) * t
        elif prev_kf.interpolation == TemporalInterpolation.EASE_IN_OUT:
            # Smoothstep interpolation
            t2 = t * t
            t3 = t2 * t
            return prev_kf.value + (next_kf.value - prev_kf.value) * (3 * t2 - 2 * t3)
        else:
            # Default to linear
            return prev_kf.value + (next_kf.value - prev_kf.value) * t
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_uid": self.target_uid,
            "property_name": self.property_name,
            "keyframes": [kf.to_dict() for kf in self.keyframes],
            "duration_frames": self.duration_frames
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemporalSequence':
        return cls(
            target_uid=data["target_uid"],
            property_name=data["property_name"],
            keyframes=[
                TemporalKeyframe(
                    frame=kf["frame"],
                    value=kf["value"],
                    interpolation=TemporalInterpolation(kf["interpolation"])
                ) for kf in data["keyframes"]
            ],
            duration_frames=data["duration_frames"]
        )


class TemporalGeometryGenerator:
    """Generate temporal sequences from geometry tokens."""
    
    def __init__(self, fps: int = 30):
        self.fps = fps
    
    def create_animation(self, 
                        tokens: List[GeometryToken],
                        duration_seconds: float = 5.0) -> List[TemporalSequence]:
        """
        Create animation sequences for geometry tokens.
        
        Args:
            tokens: List of geometry tokens to animate
            duration_seconds: Total animation duration
            
        Returns:
            List of temporal sequences
        """
        duration_frames = int(duration_seconds * self.fps)
        sequences = []
        
        for i, token in enumerate(tokens):
            # Create different animation types based on token type
            if token.token_type == GeometryTokenType.PRIMITIVE:
                sequences.extend(self._animate_primitive(token, duration_frames))
            elif token.token_type == GeometryTokenType.TRANSFORM:
                sequences.extend(self._animate_transform(token, duration_frames))
        
        return sequences
    
    def _animate_primitive(self, token: GeometryToken, duration_frames: int) -> List[TemporalSequence]:
        """Create animations for primitive tokens."""
        sequences = []
        
        # Rotate animation
        if token.kind in ["cube", "sphere", "cylinder", "torus"]:
            rotate_seq = TemporalSequence(
                target_uid=token.uid,
                property_name="rotate_y.angle",
                keyframes=[
                    TemporalKeyframe(frame=0, value=0, interpolation=TemporalInterpolation.LINEAR),
                    TemporalKeyframe(frame=duration_frames-1, value=360, interpolation=TemporalInterpolation.LINEAR),
                ],
                duration_frames=duration_frames
            )
            sequences.append(rotate_seq)
        
        # Scale animation for some primitives
        if token.kind in ["cube", "sphere"]:
            scale_seq = TemporalSequence(
                target_uid=token.uid,
                property_name="uniform_scale.factor",
                keyframes=[
                    TemporalKeyframe(frame=0, value=0.5, interpolation=TemporalInterpolation.EASE_IN_OUT),
                    TemporalKeyframe(frame=duration_frames//2, value=1.5, interpolation=TemporalInterpolation.EASE_IN_OUT),
                    TemporalKeyframe(frame=duration_frames-1, value=1.0, interpolation=TemporalInterpolation.EASE_IN_OUT),
                ],
                duration_frames=duration_frames
            )
            sequences.append(scale_seq)
        
        return sequences
    
    def _animate_transform(self, token: GeometryToken, duration_frames: int) -> List[TemporalSequence]:
        """Create animations for transform tokens."""
        sequences = []
        
        if token.kind.startswith("rotate"):
            # Animate the rotation amount
            axis = token.kind.split("_")[-1] if "_" in token.kind else "y"
            seq = TemporalSequence(
                target_uid=token.uid,
                property_name=f"rotate_{axis}.angle",
                keyframes=[
                    TemporalKeyframe(frame=0, value=0, interpolation=TemporalInterpolation.LINEAR),
                    TemporalKeyframe(frame=duration_frames-1, value=720, interpolation=TemporalInterpolation.LINEAR),
                ],
                duration_frames=duration_frames
            )
            sequences.append(seq)
        
        return sequences
    
    def create_temporal_token(self, 
                            sequences: List[TemporalSequence]) -> GeometryToken:
        """
        Create a temporal geometry token representing the animation.
        """
        # Create hash of sequences for deterministic UID
        seq_data = json.dumps([s.to_dict() for s in sequences], sort_keys=True)
        seq_hash = hashlib.sha256(seq_data.encode()).hexdigest()[:16]
        
        return GeometryToken(
            token_type=GeometryTokenType.TEMPORAL,
            kind="animation",
            params={
                "sequence_count": len(sequences),
                "duration_frames": sequences[0].duration_frames if sequences else 0,
                "data_hash": seq_hash
            },
            bounds=(0.0, 0.0, 0.0),
            uid=f"temporal_{seq_hash}"
        )


# Utility functions
def export_temporal_data(tokens: List[GeometryToken],
                        sequences: List[TemporalSequence]) -> Dict[str, Any]:
    """Export complete temporal geometry data."""
    return {
        "format": "h4-temporal-geometry-v1",
        "geometry_tokens": [t.to_dict() for t in tokens],
        "temporal_sequences": [s.to_dict() for s in sequences],
        "metadata": {
            "token_count": len(tokens),
            "sequence_count": len(sequences),
            "duration_frames": sequences[0].duration_frames if sequences else 0,
            "exported_at": datetime.utcnow().isoformat()
        }
    }
