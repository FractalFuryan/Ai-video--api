"""
HarmonyØ4 Compression API — Stable, Public Interface

Defines the contract that all compression engines must obey:
- Deterministic input/output
- Public metadata
- No parameter leakage
- Same signature for stub and closed core

This interface NEVER changes once published.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any


class CompressionEngine(ABC):
    """
    Abstract compression engine with stable ABI.
    
    Can be implemented as:
    - Open reference (geometric, DCT-based)
    - Closed binary core (vectorized, nonlinear, adaptive)
    - HSM-backed (hardware accelerated)
    
    All implementations must be:
    - Deterministic (same input → same output always)
    - Identity-safe (structure only, no semantic leakage)
    - Verifiable (no hidden parameters)
    """

    @abstractmethod
    def compress(self, data: bytes) -> bytes:
        """
        Compress bytes deterministically.
        
        Args:
            data: Raw bytes to compress
            
        Returns:
            Compressed bytes (deterministic)
            
        Raises:
            ValueError: If compression fails
        """
        pass

    @abstractmethod
    def decompress(self, data: bytes) -> bytes:
        """
        Decompress bytes deterministically.
        
        Args:
            data: Compressed bytes
            
        Returns:
            Original raw bytes (must match original exactly)
            
        Raises:
            ValueError: If decompression fails or data corrupted
        """
        pass

    @abstractmethod
    def info(self) -> Dict[str, Any]:
        """
        Public metadata about engine (NO sensitive info).
        
        Returns dict with:
        - engine: name (e.g., "reference", "core", "hsm")
        - deterministic: True (always)
        - identity_safe: True (always)
        - Any other non-algorithmic info
        
        MUST NOT return:
        - Algorithm details
        - Parameter values
        - Internal constants
        - Symbol names
        """
        pass
