"""
Compression Sealing Tests — Tamper Detection

Tests for:
- Engine verification (ID & fingerprint checks)
- Seal checks prevent core swaps
- Attestation functions
- CI guardrail (no real core in GitHub)
"""

import os
import pytest
from compression import attest, verify_attestation, get_engine


def test_engine_info_includes_sealing():
    """Engine info must include sealing metadata."""
    info = get_engine().info()
    
    # All engines must report these fields
    assert "deterministic" in info
    assert "identity_safe" in info
    assert "engine" in info
    
    # Sealed engines additionally report:
    if info["engine"] == "core":
        assert "sealed" in info
        assert "engine_id" in info
        assert "fingerprint" in info


def test_attest_returns_valid_dict():
    """Attestation must include all required fields."""
    att = attest()
    
    required = ["engine_id", "fingerprint", "timestamp_unix", "attestation_hash", "sealed"]
    for field in required:
        assert field in att, f"Missing attestation field: {field}"
    
    # Verify types
    assert isinstance(att["engine_id"], str)
    assert isinstance(att["fingerprint"], str)
    assert isinstance(att["timestamp_unix"], int)
    assert isinstance(att["attestation_hash"], str)
    assert isinstance(att["sealed"], bool)


def test_attest_deterministic():
    """Same engine state should produce consistent attestations."""
    att1 = attest()
    att2 = attest()
    
    # Engine, fingerprint, sealed status should match
    assert att1["engine_id"] == att2["engine_id"]
    assert att1["fingerprint"] == att2["fingerprint"]
    assert att1["sealed"] == att2["sealed"]
    
    # Attestation hash will differ (different timestamps)
    # but can be independently verified


def test_verify_attestation_matches_current():
    """Current attestation should verify against current engine."""
    att = attest()
    assert verify_attestation(att) is True


def test_ci_guardrail_no_real_core():
    """CI environment should NOT have real compression core loaded."""
    # In CI, HARMONY4_CORE_PATH should not be set
    # This prevents accidental leakage of the real core
    
    if os.getenv("CI"):
        assert os.getenv("HARMONY4_CORE_PATH") is None, \
            "CI should not have HARMONY4_CORE_PATH set (prevents core leakage)"


def test_sealing_info_in_metadata():
    """Sealing info must be present in container metadata."""
    from container.h4mk import build_h4mk
    from container.reader import H4MKReader
    import json
    
    # Build minimal H4MK with 256-byte aligned data
    core_blocks = [b"x" * 256]
    seek_entries = [(0, 0)]
    meta = {"project": "test"}
    safe = {"audio": False}
    
    h4mk = build_h4mk(core_blocks, seek_entries, meta, safe)
    
    # Read it back
    reader = H4MKReader(h4mk)
    chunks = reader.get_chunks(b"META")
    
    # Parse metadata
    meta_bytes = chunks[0] if chunks else b'{}'
    try:
        meta_dict = json.loads(meta_bytes)
    except json.JSONDecodeError:
        # Might be raw JSON bytes
        meta_dict = json.loads(meta_bytes.decode('utf-8', errors='replace'))
    
    # Sealing info should be present
    assert "compression" in meta_dict
    compression = meta_dict["compression"]
    
    assert "engine_id" in compression
    assert "fingerprint" in compression
    assert "sealed" in compression
    assert compression["deterministic"] is True


def test_reference_engine_marks_as_reference():
    """Reference engine should report engine as 'geometric-reference'."""
    from compression.geo_ref import GeometricReferenceCompressor
    
    ref = GeometricReferenceCompressor()
    info = ref.info()
    
    assert info["engine"] == "geometric-reference"
    # Reference is always deterministic
    assert info["deterministic"] is True
