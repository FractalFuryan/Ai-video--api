"""HarmonyØ4 Multi-Track H4MK Container Builder

Format:
  Header:   MAGIC(4) + VERSION(2) + RESERVED(2) = 8 bytes
  Body:     CORE/SEEK/META/SAFE/VERI chunks (variable, CRC-protected)
  
Each chunk:
  TAG(4) + LEN(4 big-endian) + CRC32(4 big-endian) + PAYLOAD(len bytes)

CORE = video/audio/data block (opaque, transport-only)
SEEK = seekable entry list (pts_us, offset pairs)
META = JSON metadata (container info, codec hints)
SAFE = JSON safety scopes (no codec semantics, no ML, no synthesis)
VERI = SHA256 of all prior chunks (integrity check)
"""

from __future__ import annotations
import struct
import zlib
import json
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any

from utils.crypto import sha256
from compression import load_engine  # ✅ NEW

MAGIC = b"H4MK"
VERSION = 1


def _crc32(data: bytes) -> int:
    """CRC32 checksum (unsigned 32-bit)."""
    return zlib.crc32(data) & 0xFFFFFFFF


@dataclass
class Chunk:
    """Single H4MK chunk: tag + length-prefixed payload + CRC32."""
    tag: bytes  # 4-byte ASCII tag
    payload: bytes

    def pack(self) -> bytes:
        """Serialize chunk: TAG + LEN + CRC32 + PAYLOAD."""
        assert len(self.tag) == 4, f"tag must be 4 bytes, got {len(self.tag)}"
        crc = _crc32(self.payload)
        header = self.tag + struct.pack(">II", len(self.payload), crc)
        return header + self.payload


def pack_seek_entries(entries) -> bytes:
    """Serialize SEEK chunk payload: count(4) + [(pts_us:8, offset:8), ...]
    
    Args:
        entries: List of SeekEntry objects or (pts_us, offset) tuples
    
    Returns:
        Binary SEEK payload
    """
    out = bytearray()
    out += struct.pack(">I", len(entries))
    for entry in entries:
        # Handle both SeekEntry objects and tuples
        if hasattr(entry, 'pts'):
            pts, off = entry.pts, entry.offset
        else:
            pts, off = entry
        out += struct.pack(">QQ", int(pts), int(off))
    return bytes(out)


def pack_meta(meta: Dict[str, Any]) -> bytes:
    """Serialize META/SAFE chunk payload: JSON without external deps.
    
    Args:
        meta: Dictionary to serialize
    
    Returns:
        UTF-8 JSON bytes (compact format)
    """
    return json.dumps(meta, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def build_h4mk(
    core_blocks: List[bytes],
    seek_entries: List[Tuple[int, int]],
    meta: Dict[str, Any],
    safe: Dict[str, Any],
) -> bytes:
    """Build complete H4MK container.
    
    Args:
        core_blocks: List of opaque block payloads
        seek_entries: List of (pts_us, offset_bytes) for keyframes
        meta: Metadata dict (project, domain, codecs, hints)
        safe: Safety scopes dict (constraints, no-ml, etc.)
    
    Returns:
        Complete H4MK binary (header + chunks + VERI)
    """
    compressor = load_engine()  # ✅ NEW
    comp_info = compressor.info()   # safe metadata only

    chunks: List[Chunk] = []

    # CORE chunks (compressed transparently)
    # NOTE: Container remains fully auditable; algorithm remains opaque when using core.
    for b in core_blocks:
        cb = compressor.compress(b)
        chunks.append(Chunk(b"CORE", cb))

    # SEEK table
    chunks.append(Chunk(b"SEEK", pack_seek_entries(seek_entries)))

    # Inject compression metadata safely (with sealing info)
    meta = dict(meta)
    meta["compression"] = {
        "engine": comp_info.get("engine", "unknown"),
        "engine_id": comp_info.get("engine_id", "unknown"),  # 🔐 SEALED
        "fingerprint": comp_info.get("fingerprint", "unknown"),  # 🔐 SEALED
        "deterministic": bool(comp_info.get("deterministic", True)),
        "identity_safe": bool(comp_info.get("identity_safe", True)),
        "opaque": bool(comp_info.get("opaque", False)),
        "sealed": bool(comp_info.get("sealed", False)),  # 🔐 Tamper-evident
    }

    # Metadata
    chunks.append(Chunk(b"META", pack_meta(meta)))

    # Safety scopes
    chunks.append(Chunk(b"SAFE", pack_meta(safe)))

    # VERI = SHA256 of all prior chunk headers + payloads
    pre_veri = b"".join(c.pack() for c in chunks)
    veri_payload = sha256(pre_veri)
    chunks.append(Chunk(b"VERI", veri_payload))

    # Assemble body
    body = b"".join(c.pack() for c in chunks)

    # H4MK header: MAGIC(4) + VERSION(2) + RESERVED(2)
    header = MAGIC + struct.pack(">HH", VERSION, 0)

    return header + body
