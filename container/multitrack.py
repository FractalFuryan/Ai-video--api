"""
Multitrack H4MK packing: CORE blocks + readable TRAK index + multi-track SEEKM.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Tuple
import struct
import json


@dataclass(frozen=True)
class TrackIndexEntry:
    """Single entry in track index."""
    track_id: str
    pts_us: int
    kind: str                    # "I" | "P" | "B"
    keyframe: bool
    core_index: int              # Index into CORE chunks


def pack_trak(entries: List[TrackIndexEntry]) -> bytes:
    """
    Pack TRAK chunk: readable index describing every CORE block.
    Does NOT reveal block contents, only metadata.
    Format: JSON with track_id, pts_us, kind, keyframe, core_index.
    """
    payload = {
        "trak": [{
            "track_id": e.track_id,
            "pts_us": int(e.pts_us),
            "kind": e.kind,
            "keyframe": bool(e.keyframe),
            "core_index": int(e.core_index),
        } for e in entries]
    }
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def unpack_trak(data: bytes) -> List[TrackIndexEntry]:
    """Unpack TRAK chunk."""
    payload = json.loads(data.decode("utf-8"))
    return [TrackIndexEntry(
        track_id=e["track_id"],
        pts_us=e["pts_us"],
        kind=e["kind"],
        keyframe=e["keyframe"],
        core_index=e["core_index"],
    ) for e in payload.get("trak", [])]


def build_seek_per_track(entries: List[TrackIndexEntry]) -> Dict[str, List[Tuple[int, int]]]:
    """
    Build multi-track seek table from entries.
    Returns {track_id: [(pts_us, core_index_of_keyframe), ...]}.
    Sorted by pts_us within each track.
    """
    out: Dict[str, List[Tuple[int, int]]] = {}
    for e in entries:
        if e.keyframe:
            out.setdefault(e.track_id, []).append((e.pts_us, e.core_index))
    # Sort by pts_us
    for track_id in out:
        out[track_id].sort(key=lambda x: x[0])
    return out


def pack_seek_multi(seek: Dict[str, List[Tuple[int, int]]]) -> bytes:
    """
    Pack SEEKM chunk: multi-track seek table (readable binary format).
    Format:
      u32 track_count
      for each track:
        u16 track_id_len + bytes
        u32 entry_count
        repeated: u64 pts_us, u32 core_index
    """
    buf = bytearray()
    buf += struct.pack(">I", len(seek))
    for track_id, entries in sorted(seek.items()):
        tid = track_id.encode("utf-8")
        buf += struct.pack(">H", len(tid)) + tid
        buf += struct.pack(">I", len(entries))
        for pts, core_idx in entries:
            buf += struct.pack(">QI", int(pts), int(core_idx))
    return bytes(buf)


def unpack_seek_multi(data: bytes) -> Dict[str, List[Tuple[int, int]]]:
    """Unpack SEEKM chunk."""
    pos = 0
    track_count = struct.unpack(">I", data[pos:pos+4])[0]
    pos += 4
    out: Dict[str, List[Tuple[int, int]]] = {}
    for _ in range(track_count):
        l = struct.unpack(">H", data[pos:pos+2])[0]
        pos += 2
        tid = data[pos:pos+l].decode("utf-8")
        pos += l
        n = struct.unpack(">I", data[pos:pos+4])[0]
        pos += 4
        arr = []
        for __ in range(n):
            pts, idx = struct.unpack(">QI", data[pos:pos+12])
            pos += 12
            arr.append((pts, idx))
        out[tid] = arr
    return out
