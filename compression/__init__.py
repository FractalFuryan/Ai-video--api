"""
HarmonyØ4 Compression Engine Loader

Runtime selection: open reference or closed core.

- GitHub users get reference (fully auditable)
- Production gets core (if HARMONY4_CORE_PATH set)
- Same API, same container, same outputs
- Deterministic in both cases
"""

from __future__ import annotations
import os
import logging
from typing import Optional
from compression.api import CompressionEngine
from compression.geo_ref import GeometricReferenceCompressor
from compression.loader import CoreCompression, BinaryCoreMissing
from compression.attest import attest, verify_attestation

logger = logging.getLogger(__name__)


_engine: Optional[CompressionEngine] = None


def load_engine() -> CompressionEngine:
    """
    Load compression engine (core or reference).
    
    Tries in order:
    1. Binary core at HARMONY4_CORE_PATH (if set)
    2. Reference engine (always available)
    
    Returns:
        Compression engine ready to use
    """
    global _engine

    if _engine is not None:
        return _engine

    # Try binary core first
    core_path = os.getenv("HARMONY4_CORE_PATH")
    if core_path:
        try:
            _engine = CoreCompression(core_path)
            logger.info(f"✅ Loaded binary core: {core_path}")
            return _engine
        except BinaryCoreMissing as e:
            logger.warning(f"Binary core not found, using reference: {e}")

    # Fall back to reference
    _engine = GeometricReferenceCompressor()
    logger.info("✅ Loaded reference compressor (open source)")
    return _engine


def get_engine() -> CompressionEngine:
    """Get the current compression engine (load if needed)."""
    return load_engine()


# ============================================================================
# Convenience Functions
# ============================================================================


def compress(data: bytes) -> bytes:
    """Compress bytes using loaded engine."""
    return get_engine().compress(data)


def decompress(data: bytes) -> bytes:
    """Decompress bytes using loaded engine."""
    return get_engine().decompress(data)


def engine_info() -> dict:
    """Get current engine metadata."""
    return get_engine().info()


def reset_engine():
    """Reset engine (for testing)."""
    global _engine
    _engine = None
