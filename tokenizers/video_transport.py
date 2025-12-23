"""HarmonyØ4 Video Transport Tokenizer

Video blocks as time-indexed, opaque data (frames, images, sequences).
NOT pixel synthesis. NOT video decoding. Container + timing only.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Dict, Any, List


@dataclass(frozen=True)
class VideoBlockToken:
    """Single video transport block token.
    
    Represents one opaque frame/block with timing + keyframe flag.
    No pixel data. No color space. No compression semantics.
    """
    pts_us: int  # Presentation timestamp (microseconds)
    block_index: int  # Frame/block sequence number
    is_key: bool  # Keyframe (I-frame) flag for seeking

    def serialize(self) -> bytes:
        """Pack to 13 bytes: pts(8) + index(4) + is_key(1).
        
        Format:
          - PTS: u64 big-endian (microseconds, 0 to ~584k years)
          - Index: u32 big-endian (block sequence, 0 to 4B)
          - Is-Key: u8 (0x00 or 0x01)
        """
        return (
            int(self.pts_us).to_bytes(8, "big")
            + int(self.block_index).to_bytes(4, "big")
            + (b"\x01" if self.is_key else b"\x00")
        )

    def metadata(self) -> Dict[str, Any]:
        """Token metadata (domain, type, no semantics)."""
        return {
            "domain": "video",
            "type": "transport-block",
            "no_synthesis": True,
            "no_pixel_semantics": True,
            "no_motion_semantics": True,
        }


class VideoTransportTokenizer:
    """Video transport tokenizer (opaque blocks, time-indexed).
    
    Args:
        fps_hint: Frames per second (for PTS calculation)
        gop: GOP size (keyframe interval in blocks)
    """

    def __init__(self, fps_hint: float = 30.0, gop: int = 30):
        self.frame_us = int(1_000_000 / float(fps_hint))  # microseconds per frame
        self.gop = int(gop)

    def encode_blocks(self, blocks: List[bytes]) -> Iterable[VideoBlockToken]:
        """Tokenize list of opaque video blocks.
        
        Args:
            blocks: List of opaque frame/block payloads (any codec, any size)
        
        Yields:
            VideoBlockToken for each block with incrementing PTS and keyframe marks
        """
        pts = 0
        for i in range(len(blocks)):
            is_key = (i % self.gop == 0)  # Keyframe every gop blocks
            yield VideoBlockToken(pts_us=pts, block_index=i, is_key=is_key)
            pts += self.frame_us
