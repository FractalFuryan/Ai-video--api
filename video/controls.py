"""
Video controls schema (non-identity).
Camera motion + render hints, never user profiling.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
import json


@dataclass(frozen=True)
class CameraPath:
    """Camera movement parameters (no identity)."""
    move: str = "static"         # "static" | "pan" | "dolly" | "orbit"
    intensity: float = 0.0       # 0..1 intensity
    smooth: float = 0.5          # 0..1 smoothing


@dataclass(frozen=True)
class MotionCurve:
    """Motion timing curve."""
    curve: str = "linear"        # "linear" | "ease_in" | "ease_out" | "ease_in_out"
    strength: float = 0.0        # 0..1 strength


@dataclass(frozen=True)
class VisualControlFrame:
    """Per-frame visual controls (no identity)."""
    pts_us: int
    camera: CameraPath = CameraPath()
    motion: MotionCurve = MotionCurve()
    notes: str = ""              # Safe textual hints (no PII, no identity)


def encode_controls(frames: List[VisualControlFrame]) -> bytes:
    """Encode control frames to JSON bytes."""
    payload = {"controls": [asdict(f) for f in frames]}
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def decode_controls(data: bytes) -> Dict[str, Any]:
    """Decode control frame JSON."""
    return json.loads(data.decode("utf-8"))
