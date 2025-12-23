# harmony4_media/mux/h4mk_multitrack.py
"""
Multi-track H4MK: per-track GOP + seek tables.

Core concept:
  - TrackSpec: metadata about a logical track (audio, control, safety, etc.)
  - Block: opaque compressed data + timing + type (I/P/B).
  - mux_multitrack_gop(): builds a container with routing + decode bounds.

Model-agnostic payload routing:
  - CORE chunks wrapped with track_id prefix (H4TB magic).
  - Per-track seek tables (TSEK) for fast keyframe lookup.
  - Decode chain rules: start at I-block, follow bounded P/B sequence.
"""

from __future__ import annotations

import io
import struct
import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple

from .h4mk import (
    Chunk,
    mux,
    parse,
    extract,
    extract_json,
    T_CORE,
    T_META,
    T_SAFE,
    T_VERI,
    T_NOTE,
    build_seek_table,
    parse_seek_table,
)
from .gop_flags import make_flags, parse_flags, BLK_I, BLK_P, BLK_B, blk_type_str

T_TRK = b"TRAK"   # Track header chunk (JSON)
T_TSEK = b"TSEK"  # Per-track seek table (binary)


def wrap_core_payload(track_id: int, opaque_blob: bytes) -> bytes:
    """
    Wrap an opaque CORE payload with track routing header.

    Format:
      "H4TB" magic (4)
      track_id u16
      reserved u16
      payload bytes (opaque)

    Args:
        track_id: Logical track ID.
        opaque_blob: Model-specific compressed data.

    Returns:
        Wrapped payload.

    Raises:
        ValueError: If track_id out of range.
    """
    if track_id < 0 or track_id > 65535:
        raise ValueError(f"track_id={track_id} out of range (0..65535)")
    return b"H4TB" + struct.pack("<HH", track_id, 0) + opaque_blob


def unwrap_core_payload(payload: bytes) -> Tuple[int, bytes]:
    """
    Extract track_id and opaque blob from a wrapped CORE payload.

    Args:
        payload: Wrapped payload (from wrap_core_payload).

    Returns:
        Tuple of (track_id, opaque_blob).

    Raises:
        ValueError: If magic invalid.
    """
    if payload[:4] != b"H4TB":
        raise ValueError("not a track-bound CORE payload (magic H4TB)")
    track_id, _ = struct.unpack("<HH", payload[4:8])
    return int(track_id), payload[8:]


@dataclass
class TrackSpec:
    """Metadata for a logical track."""

    track_id: int
    name: str           # e.g., "main", "stems", "safety"
    kind: str           # e.g., "audio", "control", "captions"
    codec: str          # e.g., "h4core" (opaque to container)
    sample_rate: int = 48000
    channels: int = 1
    note: str = ""


@dataclass
class Block:
    """A single compressed GOP block."""

    pts_ms: int         # Presentation timestamp (milliseconds)
    blk_type: int       # BLK_I, BLK_P, or BLK_B
    opaque_blob: bytes  # Model-specific compressed data


def mux_multitrack_gop(
    tracks: List[TrackSpec],
    blocks_by_track: Dict[int, List[Block]],
    *,
    meta_json: Optional[bytes] = None,
    safety_json: Optional[bytes] = None,
    verify_json: Optional[bytes] = None,
    note_bytes: Optional[bytes] = None,
) -> bytes:
    """
    Build a multi-track H4MK container with per-track seek tables.

    Chunks written in order:
      1. TRAK: track definitions
      2. META, SAFE, VERI, NOTE: global sidecars (if provided)
      3. CORE: blocks (sorted by pts_ms, then track_id)
      4. TSEK: per-track seek tables (one entry per I-block per track)

    Args:
        tracks: List of TrackSpec.
        blocks_by_track: Dict mapping track_id -> list of Block.
        meta_json: Optional global metadata (JSON bytes).
        safety_json: Optional safety info (JSON bytes).
        verify_json: Optional verification data (JSON bytes).
        note_bytes: Optional notes (text bytes).

    Returns:
        Complete H4MK container.

    Raises:
        ValueError: If track_id mismatch or other validation fails.
    """
    # Validate track IDs
    track_ids = {t.track_id for t in tracks}
    if len(track_ids) != len(tracks):
        raise ValueError("duplicate track_id in tracks")
    for tid in blocks_by_track.keys():
        if tid not in track_ids:
            raise ValueError(f"blocks provided for unknown track_id {tid}")

    chunks: List[Chunk] = []

    # 1) Track headers
    trk_payload = json.dumps(
        {"tracks": [t.__dict__ for t in tracks]},
        ensure_ascii=False,
    ).encode("utf-8")
    chunks.append(Chunk(ctype=T_TRK, flags=0, payload=trk_payload))

    # 2) Global sidecars
    if meta_json is not None:
        chunks.append(Chunk(ctype=T_META, flags=0, payload=meta_json))
    if safety_json is not None:
        chunks.append(Chunk(ctype=T_SAFE, flags=0, payload=safety_json))
    if verify_json is not None:
        chunks.append(Chunk(ctype=T_VERI, flags=0, payload=verify_json))
    if note_bytes is not None:
        chunks.append(Chunk(ctype=T_NOTE, flags=0, payload=note_bytes))

    # 3) CORE blocks (sorted by time, then track_id)
    core_chunks: List[Tuple[int, int, Chunk]] = []
    for tid, blks in blocks_by_track.items():
        for b in blks:
            flags = make_flags(b.pts_ms, b.blk_type)
            payload = wrap_core_payload(tid, b.opaque_blob)
            core_chunks.append(
                (b.pts_ms, tid, Chunk(ctype=T_CORE, flags=flags, payload=payload))
            )

    core_chunks.sort(key=lambda x: (x[0], x[1]))
    chunks.extend([c for _, _, c in core_chunks])

    # 4) First mux pass: learn chunk indices for seek table
    tmp = mux(chunks)
    _, infos = parse(tmp, validate_crc=True)

    # Build seek map: track_id -> [(pts_ms, chunk_index), ...]
    seek_map: Dict[int, List[Tuple[int, int]]] = {t.track_id: [] for t in tracks}

    for ci in infos:
        if ci.ctype != "CORE":
            continue
        pts, blk_type = parse_flags(ci.flags)
        raw = extract(tmp, ci.index)
        tid, _ = unwrap_core_payload(raw)

        if blk_type == BLK_I:
            seek_map.setdefault(tid, []).append((pts, ci.index))

    # 5) Append per-track seek tables
    for tid, entries in seek_map.items():
        st = build_seek_table(entries)
        payload = b"H4TS" + struct.pack("<HH", tid, 0) + st
        chunks.append(Chunk(ctype=T_TSEK, flags=0, payload=payload))

    return mux(chunks)


def read_tracks(container: bytes) -> List[TrackSpec]:
    """
    Extract track definitions from container.

    Returns:
        List of TrackSpec.
    """
    _, infos = parse(container, validate_crc=True)
    for ci in infos:
        if ci.ctype == "TRAK":
            obj = extract_json(container, ci.index)
            return [TrackSpec(**t) for t in obj.get("tracks", [])]
    return []


def _read_track_seek_tables(container: bytes) -> Dict[int, List[Tuple[int, int]]]:
    """
    Extract all per-track seek tables.

    Returns:
        Dict mapping track_id -> [(pts_ms, chunk_index), ...].
    """
    _, infos = parse(container, validate_crc=True)
    out: Dict[int, List[Tuple[int, int]]] = {}
    for ci in infos:
        if ci.ctype != "TSEK":
            continue
        payload = extract(container, ci.index)
        if payload[:4] != b"H4TS":
            continue
        tid, _ = struct.unpack("<HH", payload[4:8])
        entries = parse_seek_table(payload[8:])
        out[int(tid)] = entries
    return out


def find_keyframe_for_time(
    container: bytes, track_id: int, t_ms: int
) -> Optional[int]:
    """
    Find the I-block (keyframe) at or before a given time.

    Uses per-track seek table if available; falls back to scan.

    Args:
        container: H4MK file bytes.
        track_id: Logical track ID.
        t_ms: Target time (milliseconds).

    Returns:
        Chunk index of I-block, or None if none found.
    """
    seeks = _read_track_seek_tables(container)
    entries = seeks.get(track_id)
    if entries:
        # Binary search: rightmost pts_ms <= t_ms
        lo, hi = 0, len(entries) - 1
        best = None
        while lo <= hi:
            mid = (lo + hi) // 2
            pts, idx = entries[mid]
            if pts <= t_ms:
                best = idx
                lo = mid + 1
            else:
                hi = mid - 1
        return best

    # Fallback: scan all chunks
    _, infos = parse(container, validate_crc=True)
    best = None
    for ci in infos:
        if ci.ctype != "CORE":
            continue
        pts, blk_type = parse_flags(ci.flags)
        raw = extract(container, ci.index)
        tid, _ = unwrap_core_payload(raw)
        if tid != track_id:
            continue
        if blk_type == BLK_I and pts <= t_ms:
            best = ci.index
    return best


def get_decode_chain(
    container: bytes, track_id: int, t_ms: int
) -> List[int]:
    """
    Compute the decode chain for a given track and time.

    Rules:
      - Start at nearest I-block <= t_ms.
      - Include subsequent P/B blocks up to t_ms.
      - Stop at next I-block (next GOP).

    Args:
        container: H4MK file bytes.
        track_id: Logical track ID.
        t_ms: Target time (milliseconds).

    Returns:
        Ordered list of chunk indices to decode.
    """
    _, infos = parse(container, validate_crc=True)
    i_idx = find_keyframe_for_time(container, track_id, t_ms)
    if i_idx is None:
        return []

    # Locate i_idx in chunk list
    pos_map = {ci.index: j for j, ci in enumerate(infos)}
    start_pos = pos_map.get(i_idx)
    if start_pos is None:
        return [i_idx]

    chain = [i_idx]
    i_flags = infos[start_pos].flags
    i_pts, _ = parse_flags(i_flags)

    # Collect subsequent blocks for this track up to t_ms, stopping at next I
    for ci in infos[start_pos + 1 :]:
        if ci.ctype != "CORE":
            continue
        pts, blk_type = parse_flags(ci.flags)
        raw = extract(container, ci.index)
        tid, _ = unwrap_core_payload(raw)
        if tid != track_id:
            continue
        if blk_type == BLK_I:
            break  # Next GOP begins
        if pts > t_ms:
            break
        chain.append(ci.index)

    return chain


def pretty_list_core(container: bytes) -> List[Dict[str, Any]]:
    """
    List all CORE blocks in human-readable format.

    Returns:
        List of dicts with chunk_index, track_id, pts_ms, blk type, opaque size.
    """
    _, infos = parse(container, validate_crc=True)
    rows: List[Dict[str, Any]] = []
    for ci in infos:
        if ci.ctype != "CORE":
            continue
        pts, blk_type = parse_flags(ci.flags)
        tid, opaque = unwrap_core_payload(extract(container, ci.index))
        rows.append({
            "chunk_index": ci.index,
            "track_id": tid,
            "pts_ms": pts,
            "blk": blk_type_str(blk_type),
            "opaque_bytes": len(opaque),
        })
    return rows
