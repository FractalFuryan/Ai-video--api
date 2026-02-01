"""HarmonyØ4 Hashing Utilities

Shared cryptographic hash functions for integrity verification.
"""

from __future__ import annotations
import hashlib
import zlib

import bcrypt


def sha256(data: bytes) -> bytes:
    """Compute SHA256 digest.
    
    Args:
        data: Input bytes
    
    Returns:
        32-byte SHA256 digest
    """
    return hashlib.sha256(data).digest()


def sha256_hex(data: bytes) -> str:
    """Compute SHA256 hex digest.

    Args:
        data: Input bytes

    Returns:
        64-character hex string
    """
    return hashlib.sha256(data).hexdigest()


def sha256_hex_text(text: str) -> str:
    """Compute SHA256 hex digest of text using UTF-8.

    Args:
        text: Input string

    Returns:
        64-character hex string
    """
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def hash_api_key_secure(raw_key: str) -> str:
    """Hash API key with bcrypt (secure, slow hashing)."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(raw_key.encode("utf-8"), salt).decode("utf-8")


def verify_api_key_secure(raw_key: str, stored_hash: str) -> bool:
    """Verify API key against bcrypt hash."""
    try:
        return bcrypt.checkpw(raw_key.encode("utf-8"), stored_hash.encode("utf-8"))
    except (ValueError, bcrypt.errors.BCryptError):
        return False


def crc32(data: bytes) -> int:
    """Compute CRC32 checksum (unsigned 32-bit).
    
    Args:
        data: Input bytes
    
    Returns:
        CRC32 value as unsigned 32-bit integer
    """
    return zlib.crc32(data) & 0xFFFFFFFF
