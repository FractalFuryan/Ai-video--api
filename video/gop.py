"""
GOP (Group of Pictures) and keyframe scheduling helpers.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class GOPConfig:
    """Group of pictures configuration."""
    gop_size: int = 30          # I-frame every N blocks
    allow_b: bool = False        # Allow B-frames


def is_keyframe(index: int, cfg: GOPConfig) -> bool:
    """Check if block at index is a keyframe."""
    return (index % cfg.gop_size) == 0


def kind_for(index: int, cfg: GOPConfig) -> str:
    """Determine frame kind (I | P | B) for a given index."""
    if is_keyframe(index, cfg):
        return "I"
    elif cfg.allow_b and (index % 2) == 1:
        return "B"
    else:
        return "P"
