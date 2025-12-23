# container/chunks.py
"""
Chunk primitives: opaque data + routing.

Integrates with H4MK multi-track format.
CoreChunk wraps frame data for mux/demux operations.
"""

from __future__ import annotations

import struct
from typing import Optional


class CoreChunk:
    """
    Opaque media chunk (audio frame, video frame, control data, etc).

    Holds raw bytes + minimal routing info.
    """

    def __init__(
        self,
        payload: bytes,
        pts: int = 0,
        is_keyframe: bool = False,
        track_id: int = 1,
    ):
        """
        Args:
            payload: Opaque data (e.g., compressed frame).
            pts: Presentation timestamp (microseconds).
            is_keyframe: Whether this chunk is a seek anchor.
            track_id: Logical track ID (for multi-track containers).
        """
        self.payload = payload
        self.pts = pts
        self.is_keyframe = is_keyframe
        self.track_id = track_id

    def serialize_header(self) -> bytes:
        """
        Serialize chunk header (for tracking).

        Format (18 bytes):
          track_id u16 (2) | pts u64 (8) | is_keyframe u8 (1) | reserved u16 (2)
        """
        return struct.pack(
            "<HQBH",
            self.track_id,
            self.pts,
            1 if self.is_keyframe else 0,
            0,
        )

    @classmethod
    def deserialize_header(cls, data: bytes) -> dict:
        """Reconstruct header from bytes."""
        if len(data) < 13:
            raise ValueError("header too short")
        track_id, pts, is_key, _ = struct.unpack("<HQBH", data[:13])
        return {
            "track_id": int(track_id),
            "pts": int(pts),
            "is_keyframe": bool(is_key),
        }

    def __repr__(self) -> str:
        return (
            f"CoreChunk(track={self.track_id}, pts={self.pts}, "
            f"keyframe={self.is_keyframe}, size={len(self.payload)})"
        )


class ChunkStream:
    """
    Accumulates chunks for batch processing or muxing.
    """

    def __init__(self):
        self.chunks: list[CoreChunk] = []

    def add(self, chunk: CoreChunk) -> None:
        """Append a chunk."""
        self.chunks.append(chunk)

    def by_track(self, track_id: int) -> list[CoreChunk]:
        """Filter chunks by track ID."""
        return [c for c in self.chunks if c.track_id == track_id]

    def by_time_range(self, pts_min: int, pts_max: int) -> list[CoreChunk]:
        """Filter chunks by time range."""
        return [c for c in self.chunks if pts_min <= c.pts <= pts_max]

    def keyframes(self) -> list[CoreChunk]:
        """Return all keyframe chunks."""
        return [c for c in self.chunks if c.is_keyframe]

    def total_size(self) -> int:
        """Sum of all payload sizes."""
        return sum(len(c.payload) for c in self.chunks)

    def __len__(self) -> int:
        return len(self.chunks)

    def __repr__(self) -> str:
        return f"ChunkStream({len(self.chunks)} chunks, {self.total_size()} bytes)"
