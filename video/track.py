"""
Track and block metadata (public, auditable).
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Track:
    """Track metadata."""
    track_id: str
    kind: str = "video_main"     # "video_main" | "audio_main" | "controls" | "captions" etc.


@dataclass(frozen=True)
class TrackBlock:
    """A single block within a track."""
    track_id: str
    pts_us: int                  # Presentation timestamp (microseconds)
    kind: str                    # "I" | "P" | "B"
    keyframe: bool               # Random access point?
    payload: bytes               # Opaque block data
