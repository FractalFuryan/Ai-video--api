"""HarmonyØ4 Transport-Only Encryption Masking

Provides per-block key derivation via HKDF + XOR masking.
NOT codec encryption. NO semantic leakage. Container + transport only.
"""

from __future__ import annotations
import hashlib
from dataclasses import dataclass
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes


def sha256(data: bytes) -> bytes:
    """SHA256 digest."""
    return hashlib.sha256(data).digest()


@dataclass(frozen=True)
class MaskSpec:
    """Transport-only masking specification.
    
    NOT codec encryption. No secret algorithm leakage.
    Per-block key derivation only.
    """
    enabled: bool = False
    context: bytes = b"Harmony\xc3\x984|Mask|v1"  # "HarmonyØ4|Mask|v1" in UTF-8
    length: int = 32  # per-block key length (bits)


def derive_block_key(master_key: bytes, block_index: int, spec: MaskSpec) -> bytes:
    """Derive per-block key via HKDF-SHA256.
    
    Args:
        master_key: Input keying material (>=16 bytes recommended)
        block_index: Block sequence number (0-indexed)
        spec: MaskSpec configuration
    
    Returns:
        Derived key of length spec.length bytes
    """
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=spec.length,
        salt=None,
        info=spec.context + b"|" + str(block_index).encode("utf-8"),
    )
    return hkdf.derive(master_key)


def xor_mask(data: bytes, key: bytes) -> bytes:
    """Apply XOR mask to data using key-derived keystream.
    
    Expands key via repeated SHA256 hashing (deterministic, structure-only).
    
    Args:
        data: Payload to mask
        key: Masking key
    
    Returns:
        XOR-masked data (same length as input)
    """
    out = bytearray(len(data))
    stream = b""
    counter = 0
    i = 0
    
    while i < len(data):
        counter_bytes = counter.to_bytes(4, "big")
        stream = hashlib.sha256(key + counter_bytes).digest()
        for b in stream:
            if i >= len(data):
                break
            out[i] = data[i] ^ b
            i += 1
        counter += 1
    
    return bytes(out)
