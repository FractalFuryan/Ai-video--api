# api/video.py
"""
Video API: frame tokenization + seeking.

Endpoints:
  POST /video/tokenize - Extract tokens from opaque frame data
  GET /video/seek - Binary-search frame by timestamp
  GET /video/metadata - Frame sequence metadata
"""

from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, Query
from pydantic import BaseModel
import io

from tokenizers.video import VideoTokenizer, VideoBlockToken
from container import SeekTable, CoreChunk, ChunkStream


router = APIRouter(prefix="/video", tags=["video"])


class TokenizeResponse(BaseModel):
    """Response from tokenization endpoint."""

    block_count: int
    tokens: list[str]  # serialized tokens (hex)
    seek_entries: list[tuple[int, int]]  # [(pts, offset), ...]
    duration_us: int


class SeekResponse(BaseModel):
    """Response from seek endpoint."""

    found: bool
    pts: int
    offset: int


class MetadataResponse(BaseModel):
    """Response from metadata endpoint."""

    frame_count: int
    duration_us: int
    duration_sec: float
    fps: float
    keyframe_count: int
    keyframe_positions: list[int]


@router.post("/tokenize", response_model=TokenizeResponse)
async def tokenize_video(
    file: UploadFile = File(...),
    fps: float = Query(30.0, description="Frames per second"),
    gop_size: int = Query(30, description="Keyframe interval"),
    block_size: int = Query(512 * 1024, description="Frame block size (bytes)"),
):
    """
    Tokenize opaque video frame data.

    Splits input into fixed-size blocks and generates seeking tokens.

    Args:
        file: Raw video data (any codec/container).
        fps: Frame rate for PTS calculation.
        gop_size: Keyframe interval (every Nth frame).
        block_size: Maximum bytes per frame block.

    Returns:
        Tokens, seek table, and metadata.
    """
    # Read file
    raw_data = await file.read()

    # Split into blocks
    blocks = [
        raw_data[i : i + block_size]
        for i in range(0, len(raw_data), block_size)
    ]

    # Initialize tokenizer and seek table
    tokenizer = VideoTokenizer(fps=fps, gop_size=gop_size)
    seek = SeekTable()

    tokens_serialized = []
    offset = 0

    # Tokenize and build seek table
    for token in tokenizer.encode(blocks):
        tokens_serialized.append(token.serialize().hex())
        if token.is_keyframe:
            seek.add(token.pts, offset)
        offset += len(blocks[token.block_index]) if token.block_index < len(blocks) else 0

    seek.finalize()

    # Compute duration
    if tokens_serialized:
        last_token = VideoBlockToken.deserialize(bytes.fromhex(tokens_serialized[-1]))
        duration_us = last_token.pts
    else:
        duration_us = 0

    return TokenizeResponse(
        block_count=len(blocks),
        tokens=tokens_serialized,
        seek_entries=seek.to_list(),
        duration_us=duration_us,
    )


@router.get("/seek", response_model=SeekResponse)
async def seek_frame(
    pts: int = Query(..., description="Target PTS (microseconds)"),
    seek_table: str = Query(..., description="Serialized seek table (hex)"),
):
    """
    Find nearest keyframe at or before a timestamp.

    Args:
        pts: Target presentation timestamp (microseconds).
        seek_table: Hex-encoded serialized seek table.

    Returns:
        Sought position (offset and PTS).
    """
    try:
        seek_bytes = bytes.fromhex(seek_table)
        table = SeekTable.deserialize(seek_bytes)
    except Exception as e:
        return SeekResponse(found=False, pts=0, offset=0)

    entry = table.seek(pts)
    if entry is None:
        return SeekResponse(found=False, pts=0, offset=0)

    return SeekResponse(found=True, pts=entry.pts, offset=entry.offset)


@router.post("/metadata", response_model=MetadataResponse)
async def get_metadata(
    file: UploadFile = File(...),
    fps: float = Query(30.0),
    gop_size: int = Query(30),
    block_size: int = Query(512 * 1024),
):
    """
    Extract frame sequence metadata (duration, keyframe positions, etc).

    Args:
        file: Video data.
        fps: Frame rate.
        gop_size: Keyframe interval.
        block_size: Frame block size.

    Returns:
        Metadata dict.
    """
    raw_data = await file.read()
    blocks = [
        raw_data[i : i + block_size]
        for i in range(0, len(raw_data), block_size)
    ]

    tokenizer = VideoTokenizer(fps=fps, gop_size=gop_size)
    tokens = list(tokenizer.encode(blocks))
    metadata = tokenizer.decode(tokens)

    return MetadataResponse(**metadata)
