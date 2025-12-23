"""HarmonyØ4 Hashing Utilities

Shared cryptographic hash functions for integrity verification.
"""

from __future__ import annotations
import hashlib
import zlib


def sha256(data: bytes) -> bytes:
    """Compute SHA256 digest.
    
    Args:
        data: Input bytes
    
    Returns:
        32-byte SHA256 digest
    """
    return hashlib.sha256(data).digest()


def crc32(data: bytes) -> int:
    """Compute CRC32 checksum (unsigned 32-bit).
    
    Args:
        data: Input bytes
    
    Returns:
        CRC32 value as unsigned 32-bit integer
    """
    return zlib.crc32(data) & 0xFFFFFFFF
