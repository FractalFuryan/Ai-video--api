# harmony4_media/mux/h4mk.py
"""
H4MK Container Format: Harmony 4 Media Kernel.

A simple, deterministic, container format:
  - Chunk-based (each chunk has type, flags, payload).
  - CRC32 per-chunk validation.
  - Global header with version + metadata.
  - Supports multi-track GOP audio with seek tables.

Layout:
  [H4MK HEADER (16 bytes)]
  [CHUNK 0]
  [CHUNK 1]
  ...
  [CHECKSUM (4 bytes)]
"""

from __future__ import annotations

import io
import struct
import json
import zlib
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple

# Chunk types (4-byte tags)
T_CORE = b"CORE"  # Core audio/media payload (opaque)
T_META = b"META"  # Metadata (JSON)
T_SAFE = b"SAFE"  # Safety/audit info (JSON)
T_VERI = b"VERI"  # Verification data (JSON, e.g., checksums)
T_NOTE = b"NOTE"  # Human notes (text)
T_TRK = b"TRAK"   # Track headers (JSON)
T_TSEK = b"TSEK"  # Per-track seek table (binary)


@dataclass
class Chunk:
    """Represents a single H4MK chunk."""

    ctype: bytes  # 4-byte type identifier
    flags: int    # u32 flags (meaning depends on ctype)
    payload: bytes  # chunk data (opaque)

    def __post_init__(self):
        if len(self.ctype) != 4:
            raise ValueError("ctype must be exactly 4 bytes")


@dataclass
class ChunkInfo:
    """Metadata about a chunk in a container (after parse)."""

    ctype: str    # type as string (e.g., "CORE")
    flags: int
    index: int    # byte offset in container (after header)
    payload_len: int
    crc32: int    # computed CRC32


def _encode_chunk(chunk: Chunk) -> bytes:
    """Encode a single chunk to bytes."""
    header = struct.pack(
        "<4sII",
        chunk.ctype,
        chunk.flags,
        len(chunk.payload),
    )
    crc = zlib.crc32(header + chunk.payload) & 0xFFFFFFFF
    return header + chunk.payload + struct.pack("<I", crc)


def _h4mk_header() -> bytes:
    """
    Create H4MK file header (16 bytes total).
    
    Layout:
      magic (4) | version (1) | flags (1) | reserved (2) | timestamp (8)
    """
    magic = b"H4MK"
    version = 1  # u8
    flags = 0    # u8
    reserved = 0  # u16
    timestamp = 0  # u64 (unix epoch, ms)
    return magic + struct.pack("<BBHQ", version, flags, reserved, timestamp)


def mux(chunks: List[Chunk]) -> bytes:
    """
    Build a complete H4MK container from a list of chunks.

    Returns:
        Complete H4MK file as bytes.
    """
    header = _h4mk_header()
    body = b"".join(_encode_chunk(c) for c in chunks)
    footer = struct.pack("<I", zlib.crc32(header + body) & 0xFFFFFFFF)
    return header + body + footer


def parse(container: bytes, validate_crc: bool = True) -> Tuple[Dict[str, Any], List[ChunkInfo]]:
    """
    Parse an H4MK container and return header + chunk info.

    Args:
        container: H4MK file bytes.
        validate_crc: If True, check chunk CRCs.

    Returns:
        Tuple of (header_dict, list of ChunkInfo).

    Raises:
        ValueError: If format invalid or CRC fails.
    """
    if len(container) < 16:
        raise ValueError("container too short for header")

    # Parse header (16 bytes: magic + version + flags + reserved + timestamp)
    magic, version, flags, _reserved, timestamp = struct.unpack(
        "<4sBBHQ", container[:16]
    )
    if magic != b"H4MK":
        raise ValueError(f"invalid magic: {magic}")

    header = {
        "magic": magic.decode("ascii"),
        "version": version,
        "flags": flags,
        "timestamp": timestamp,
    }

    # Parse chunks
    pos = 16
    chunks: List[ChunkInfo] = []

    while pos < len(container) - 4:  # -4 for final CRC
        if pos + 12 > len(container):
            break

        ctype_bytes, chunk_flags, payload_len = struct.unpack(
            "<4sII", container[pos : pos + 12]
        )
        ctype = ctype_bytes.decode("ascii", errors="ignore")
        payload_start = pos + 12
        payload_end = payload_start + payload_len

        if payload_end > len(container) - 4:
            raise ValueError(f"chunk at {pos} extends past container")

        payload = container[payload_start:payload_end]

        # Validate CRC
        chunk_data = container[pos : pos + 12] + payload
        crc_pos = payload_end
        stored_crc = struct.unpack("<I", container[crc_pos : crc_pos + 4])[0]
        computed_crc = zlib.crc32(chunk_data) & 0xFFFFFFFF

        if validate_crc and computed_crc != stored_crc:
            raise ValueError(
                f"CRC mismatch at chunk {len(chunks)}: "
                f"expected {stored_crc:08x}, got {computed_crc:08x}"
            )

        chunks.append(
            ChunkInfo(
                ctype=ctype,
                flags=chunk_flags,
                index=payload_start,
                payload_len=payload_len,
                crc32=stored_crc,
            )
        )

        pos = crc_pos + 4

    # Validate container CRC
    if validate_crc and len(container) >= 4:
        stored_final = struct.unpack("<I", container[-4:])[0]
        computed_final = zlib.crc32(container[:-4]) & 0xFFFFFFFF
        if computed_final != stored_final:
            raise ValueError(
                f"Container CRC mismatch: "
                f"expected {stored_final:08x}, got {computed_final:08x}"
            )

    return header, chunks


def extract(container: bytes, index: int) -> bytes:
    """
    Extract a chunk payload by byte offset (from ChunkInfo.index).

    Args:
        container: H4MK file bytes.
        index: Byte offset of payload (from ChunkInfo.index).

    Returns:
        Chunk payload bytes.
    """
    # We need to read backward to find the length.
    # Safe approach: re-parse and find the chunk.
    _, infos = parse(container, validate_crc=False)
    for info in infos:
        if info.index == index:
            return container[index : index + info.payload_len]
    raise ValueError(f"no chunk at index {index}")


def extract_json(container: bytes, index: int) -> Dict[str, Any]:
    """Extract and parse a JSON chunk."""
    payload = extract(container, index)
    return json.loads(payload.decode("utf-8"))


def list_chunks(container: bytes) -> List[Dict[str, Any]]:
    """List all chunks in a container (for inspection)."""
    _, infos = parse(container, validate_crc=False)
    return [
        {
            "type": c.ctype,
            "flags": c.flags,
            "index": c.index,
            "payload_len": c.payload_len,
            "crc32": f"{c.crc32:08x}",
        }
        for c in infos
    ]


def build_seek_table(entries: List[Tuple[int, int]]) -> bytes:
    """
    Build a binary seek table from (pts_ms, chunk_index) pairs.

    Format:
      "H4SK" magic (4)
      count u16 (2)
      reserved u16 (2)
      [entry 0: pts_ms u32 (4), chunk_index u32 (4)]
      ...

    Args:
        entries: List of (pts_ms, chunk_index) tuples.

    Returns:
        Binary seek table.
    """
    count = len(entries)
    if count > 65535:
        raise ValueError("too many seek entries")

    header = b"H4SK" + struct.pack("<HH", count, 0)
    body = b"".join(struct.pack("<II", pts, idx) for pts, idx in entries)
    return header + body


def parse_seek_table(data: bytes) -> List[Tuple[int, int]]:
    """Parse a binary seek table."""
    if data[:4] != b"H4SK":
        raise ValueError("invalid seek table magic")

    count, _ = struct.unpack("<HH", data[4:8])
    entries = []
    for i in range(count):
        offset = 8 + i * 8
        pts, idx = struct.unpack("<II", data[offset : offset + 8])
        entries.append((int(pts), int(idx)))
    return entries
