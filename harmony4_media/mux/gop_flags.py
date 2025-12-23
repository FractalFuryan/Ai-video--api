# harmony4_media/mux/gop_flags.py
"""
GOP Flags: compact PTS + block type encoding.

Layout (u32):
  bits 0..27  = PTS milliseconds  (0..268,435,455 ms ~ 74.6 hours)
  bits 28..29 = block type (00=I, 01=P, 10=B, 11=reserved)
  bits 30..31 = reserved

This allows deterministic time-based navigation and decode-chain bounds.
"""

from __future__ import annotations

# Bit masks
PTS_MASK = (1 << 28) - 1  # 0x0FFFFFFF

TYPE_SHIFT = 28
TYPE_MASK = 0b11 << TYPE_SHIFT  # 0x30000000

# Block type constants
BLK_I = 0b00  # Intra / Keyframe (no dependencies)
BLK_P = 0b01  # Predictive (depends on previous I or P)
BLK_B = 0b10  # Bidirectional (optional, for advanced GOP)


def make_flags(pts_ms: int, blk_type: int) -> int:
    """
    Encode PTS and block type into a single u32 flags field.

    Args:
        pts_ms: Presentation timestamp in milliseconds (0 to ~74.6 hours).
        blk_type: Block type (BLK_I, BLK_P, or BLK_B).

    Returns:
        Encoded u32 flags.

    Raises:
        ValueError: If pts_ms or blk_type out of range.
    """
    if pts_ms < 0 or pts_ms > PTS_MASK:
        raise ValueError(
            f"pts_ms={pts_ms} out of range (0..{PTS_MASK}, ~74.6 hours)"
        )
    if blk_type not in (BLK_I, BLK_P, BLK_B):
        raise ValueError(f"blk_type={blk_type} invalid; use BLK_I/P/B")

    return (pts_ms & PTS_MASK) | ((blk_type & 0b11) << TYPE_SHIFT)


def parse_flags(flags: int) -> tuple[int, int]:
    """
    Decode PTS and block type from a u32 flags field.

    Args:
        flags: Encoded u32 flags.

    Returns:
        Tuple of (pts_ms, blk_type).
    """
    pts_ms = flags & PTS_MASK
    blk_type = (flags & TYPE_MASK) >> TYPE_SHIFT
    return int(pts_ms), int(blk_type)


def blk_type_str(t: int) -> str:
    """Return human-readable block type name."""
    return {BLK_I: "I", BLK_P: "P", BLK_B: "B"}.get(t, "?")
