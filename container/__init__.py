# container/__init__.py
"""
Container primitives: seek tables, chunks, and muxing.

Provides low-level building blocks for H4MK-compatible media containers.
"""

from .seek import SeekTable, SeekEntry
from .chunks import CoreChunk, ChunkStream

__all__ = [
    "SeekTable",
    "SeekEntry",
    "CoreChunk",
    "ChunkStream",
]
