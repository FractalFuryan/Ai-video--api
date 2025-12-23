# tokenizers/video.py
"""
Video tokenizer: frames -> time-indexed tokens.

Core insight:
  - Frame = opaque transport unit (codec-agnostic)
  - Token = (PTS, block_index, is_keyframe)
  - No pixel semantics, no transform, no vision logic

GOP-style markers for seeking:
  - Every Nth frame marked as keyframe (configurable, default 30fps = 1s intervals)
  - Allows O(log n) seeking without scanning every block
"""

from __future__ import annotations

import struct
from typing import Any, Dict, Iterable

from .base import Token, Tokenizer


class VideoBlockToken(Token):
    """
    Time-indexed video frame token.

    Transport-only: no pixel data, no encoding semantics.
    """

    def __init__(self, pts: int, block_index: int, is_keyframe: bool = False):
        """
        Args:
            pts: Presentation timestamp (microseconds).
            block_index: Sequential block number.
            is_keyframe: Whether this frame can be used as a seek anchor.
        """
        self.pts = pts
        self.block_index = block_index
        self.is_keyframe = is_keyframe

    def serialize(self) -> bytes:
        """
        Compact binary encoding.

        Format (13 bytes):
          pts u64 (8) | block_index u32 (4) | is_keyframe u8 (1)
        """
        return struct.pack(
            "<QIB",
            self.pts,
            self.block_index,
            1 if self.is_keyframe else 0,
        )

    def metadata(self) -> Dict[str, Any]:
        return {
            "pts_us": self.pts,
            "block_index": self.block_index,
            "is_keyframe": self.is_keyframe,
            "pts_sec": self.pts / 1_000_000,
        }

    @classmethod
    def deserialize(cls, data: bytes) -> VideoBlockToken:
        """Reconstruct token from serialized bytes."""
        if len(data) != 13:
            raise ValueError(f"token payload must be 13 bytes, got {len(data)}")
        pts, block_idx, is_key = struct.unpack("<QIB", data)
        return cls(pts, block_idx, bool(is_key))


class VideoTokenizer(Tokenizer):
    """
    Converts opaque frame blocks into seek-friendly tokens.

    Assumptions:
      - Constant frame rate (for timing)
      - Periodic keyframes (for seeking)
      - Opaque block boundaries (no interpretation)
    """

    def __init__(self, fps: float = 30.0, gop_size: int = 30):
        """
        Args:
            fps: Frames per second (for PTS calculation).
            gop_size: Keyframe interval (every Nth frame).
        """
        self.fps = fps
        self.gop_size = gop_size
        self.frame_duration_us = int(1_000_000 / fps)

    def encode(self, blocks: Iterable[bytes]) -> Iterable[VideoBlockToken]:
        """
        Convert opaque frame blocks to tokens.

        Args:
            blocks: Iterable of raw frame bytes (any codec).

        Yields:
            VideoBlockToken instances.
        """
        for block_idx, _frame_data in enumerate(blocks):
            pts = block_idx * self.frame_duration_us
            is_keyframe = (block_idx % self.gop_size == 0)
            yield VideoBlockToken(pts, block_idx, is_keyframe)

    def decode(self, tokens: Iterable[VideoBlockToken]) -> Dict[str, Any]:
        """
        Reconstruct metadata from tokens (frames themselves are opaque).

        Returns:
            Dict with frame count, duration, keyframe positions.
        """
        token_list = list(tokens)
        if not token_list:
            return {
                "frame_count": 0,
                "duration_us": 0,
                "keyframes": [],
            }

        keyframes = [t.block_index for t in token_list if t.is_keyframe]
        last_pts = token_list[-1].pts
        return {
            "frame_count": len(token_list),
            "duration_us": last_pts,
            "duration_sec": last_pts / 1_000_000,
            "fps": self.fps,
            "keyframe_positions": keyframes,
            "keyframe_count": len(keyframes),
        }
