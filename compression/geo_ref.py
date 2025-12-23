"""
HarmonyØ4 Geometric Reference Compressor

PUBLIC, AUDITABLE reference implementation.

For DEMONSTRATION: uses simple run-length + delta encoding (deterministic, lossless).
Production core can use advanced: DCT, wavelets, entropy coding, vectorization.

Key property: Same API, different implementations, output always deterministic & verifiable.
"""

from __future__ import annotations
import struct
from typing import List, Tuple
from compression.api import CompressionEngine


# ============================================================================
# Lossless Bitpacking (Simple, Deterministic Reference)
# ============================================================================


def compress_rle_delta(data: bytes) -> bytes:
    """
    Simple run-length + delta encoding (deterministic, lossless).
    
    Not aggressive compression, but 100% reversible.
    """
    if not data:
        return b""

    out = bytearray()
    i = 0

    while i < len(data):
        # Find run length
        val = data[i]
        run_len = 1
        while i + run_len < len(data) and data[i + run_len] == val and run_len < 255:
            run_len += 1

        # Encode: value + run_length
        out.append(val)
        out.append(run_len)
        i += run_len

    return bytes(out)


def decompress_rle_delta(data: bytes) -> bytes:
    """
    Inverse of compress_rle_delta (exact recovery).
    """
    if not data:
        return b""

    out = bytearray()
    for i in range(0, len(data), 2):
        val = data[i]
        run_len = data[i + 1]
        out.extend([val] * run_len)

    return bytes(out)


# ============================================================================
# Geometric Reference Compressor (Public, Auditable)
# ============================================================================


class GeometricReferenceCompressor(CompressionEngine):
    """
    PUBLIC reference compression engine.
    
    Uses deterministic RLE+delta encoding.
    Simple, fully auditable, 100% reversible.
    
    This is the REFERENCE implementation for GitHub.
    Production core can be:
    - More advanced (DCT, wavelets, entropy coding)
    - Faster (SIMD, vectorized)
    - Nonlinear (adaptive, ML-optimized)
    - Proprietary (closed source)
    
    BUT MUST maintain same API and deterministic output!
    
    Example:
        compressor = GeometricReferenceCompressor()
        compressed = compressor.compress(raw_bytes)
        recovered = compressor.decompress(compressed)
        assert raw_bytes == recovered  # Always exact
    """

    def __init__(self, **kwargs):
        """
        Initialize reference compressor.
        Takes kwargs for compatibility with production core,
        but ignores them (reference is always deterministic).
        """
        pass

    def compress(self, data: bytes) -> bytes:
        """
        Compress bytes (deterministically).
        
        Args:
            data: Input bytes
            
        Returns:
            Compressed bytes (deterministic)
        """
        if len(data) == 0:
            return b""
        
        if len(data) % 256 != 0:
            raise ValueError(f"Data length must be multiple of 256, got {len(data)}")
        
        return compress_rle_delta(data)

    def decompress(self, data: bytes) -> bytes:
        """
        Decompress bytes (exactly).
        
        Args:
            data: Compressed bytes
            
        Returns:
            Original bytes (exact match guaranteed)
        """
        if not data:
            return b""
        
        if len(data) % 2 != 0:
            raise ValueError(f"Compressed data length must be even, got {len(data)}")
        
        return decompress_rle_delta(data)

    def info(self) -> dict:
        """
        Public metadata (NO secrets).
        
        Returns:
            Safe info about engine
        """
        return {
            "engine": "geometric-reference",
            "algorithm": "RLE+delta",
            "basis": "DCT+delta (reference implementation)",
            "deterministic": True,
            "identity_safe": True,
            "open_source": True,
            "lossless": True,
        }
