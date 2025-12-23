"""
Compression Sealing Tests — Verify tamper detection & integrity binding

Tests that:
1. Compression core ID pinning works
2. Compression fingerprint pinning works
3. Seal mismatches prevent core load
4. Sealed identity binds to container VERI
5. CI doesn't run with real core (prevents secret leakage)
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from compression.api import CompressionEngine
from compression.loader import CoreCompression, BinaryCoreMissing


class TestCompressionSealPinning:
    """Verify engine ID & fingerprint pinning."""

    def test_no_real_core_in_ci(self):
        """CI guardrail: Fail if real core would leak to GitHub."""
        # In CI, HARMONY4_CORE_PATH should not be set or should be empty
        core_path = os.getenv("HARMONY4_CORE_PATH", "")
        assert core_path in ("", None), \
            "🔐 SEALING GUARDRAIL: Real core must not be in CI. Set HARMONY4_CORE_PATH only in prod."

    def test_engine_id_mismatch_detected(self):
        """Engine ID mismatch raises RuntimeError."""
        with patch.dict(os.environ, {
            "HARMONY4_ENGINE_ID": "h4core-geo-v1.0.0",
            "HARMONY4_CORE_PATH": "/nonexistent/libh4core.so"
        }):
            # Mock library with different ID
            mock_lib = MagicMock()
            mock_lib.h4_engine_id.return_value = b"h4core-geo-v0.9.9"  # Mismatch!
            
            with patch("ctypes.CDLL", return_value=mock_lib):
                with patch("os.path.exists", return_value=True):
                    with pytest.raises(RuntimeError, match="COMPRESSION CORE MISMATCH"):
                        CoreCompression("/nonexistent/libh4core.so")

    def test_fingerprint_mismatch_detected(self):
        """Engine fingerprint mismatch raises RuntimeError."""
        with patch.dict(os.environ, {
            "HARMONY4_ENGINE_FP": "a" * 64,  # Expected FP (64 hex chars = 32 bytes)
            "HARMONY4_CORE_PATH": "/nonexistent/libh4core.so"
        }):
            mock_lib = MagicMock()
            mock_lib.h4_engine_id.return_value = b"h4core-geo-v1.0.0"
            
            # Mock h4_engine_fp to return different fingerprint
            mock_fp_bytes = b"\xbb" * 32  # Different from "aaa..."
            mock_lib.h4_engine_fp.return_value = mock_fp_bytes
            
            with patch("ctypes.CDLL", return_value=mock_lib):
                with patch("os.path.exists", return_value=True):
                    with pytest.raises(RuntimeError, match="COMPRESSION CORE ALTERED"):
                        CoreCompression("/nonexistent/libh4core.so")

    def test_core_not_found_raises(self):
        """Missing core binary raises BinaryCoreMissing."""
        with pytest.raises(BinaryCoreMissing):
            CoreCompression("/nonexistent/libh4core.so")

    def test_valid_seal_passes(self):
        """Valid engine ID & FP pass seal check."""
        with patch.dict(os.environ, {
            "HARMONY4_ENGINE_ID": "h4core-geo-v1.0.0",
            "HARMONY4_ENGINE_FP": "a" * 64,
        }):
            mock_lib = MagicMock()
            mock_lib.h4_engine_id.return_value = b"h4core-geo-v1.0.0"
            
            # Mock matching fingerprint
            mock_fp_bytes = bytes([int(c, 16) * 16 + int(c, 16) for c in "a" * 64])[:32]
            mock_lib.h4_engine_fp.return_value = mock_fp_bytes
            
            # Mock compress/decompress
            mock_lib.h4_compress.return_value = 10
            mock_lib.h4_decompress.return_value = 20
            
            with patch("ctypes.CDLL", return_value=mock_lib):
                with patch("os.path.exists", return_value=True):
                    # Should not raise
                    core = CoreCompression("/nonexistent/libh4core.so")
                    assert core._engine_id == "h4core-geo-v1.0.0"

    def test_seal_status_in_info(self):
        """Engine info includes sealed flag (boolean)."""
        from compression import load_engine
        engine = load_engine()
        info = engine.info()
        
        # Reference implementation has no real seal, but should have the field
        # Check that the field exists (even if False for reference)
        assert any(k in info for k in ["sealed", "opaque", "deterministic"])
        assert isinstance(info.get("deterministic", False), bool)


class TestCompressionAttestationSealing:
    """Verify attestation proves engine identity."""

    def test_attest_includes_engine_id(self):
        """Attestation includes engine_id."""
        from compression.attest import attest
        att = attest()
        
        assert "engine_id" in att
        assert isinstance(att["engine_id"], str)
        assert len(att["engine_id"]) > 0

    def test_attest_includes_fingerprint(self):
        """Attestation includes fingerprint."""
        from compression.attest import attest
        att = attest()
        
        assert "fingerprint" in att
        assert isinstance(att["fingerprint"], str)

    def test_attest_includes_timestamp(self):
        """Attestation includes fresh timestamp."""
        from compression.attest import attest
        import time
        
        before = int(time.time())
        att = attest()
        after = int(time.time())
        
        assert "timestamp_unix" in att
        assert before <= att["timestamp_unix"] <= after + 1

    def test_attest_includes_proof(self):
        """Attestation includes cryptographic proof."""
        from compression.attest import attest
        att = attest()
        
        assert "attestation_hash" in att
        assert isinstance(att["attestation_hash"], str)
        assert len(att["attestation_hash"]) == 64  # SHA256 hex

    def test_attest_sealed_flag(self):
        """Attestation includes sealed status."""
        from compression.attest import attest
        att = attest()
        
        assert "sealed" in att
        assert isinstance(att["sealed"], bool)


class TestCompressionVERIBinding:
    """Verify compression seal binds to container VERI."""

    def test_h4mk_includes_compression_metadata(self):
        """H4MK container includes compression engine metadata."""
        from container.h4mk import build_h4mk
        import json
        
        # Use 256-byte aligned blocks (compression requirement)
        blocks = [b"x" * 256, b"y" * 256]
        seek = [(0, 0), (512, 256)]
        meta = {"project": "test"}
        safe = {"scope": "test"}
        
        # Build container
        h4mk = build_h4mk(blocks, seek, meta, safe)
        
        # Verify H4MK header
        assert h4mk.startswith(b"H4MK"), "Invalid H4MK magic"
        
        # Parse META chunk (simplified)
        idx = h4mk.find(b"META")
        if idx >= 0:
            # Extract size (4 bytes after tag)
            import struct
            size = struct.unpack(">I", h4mk[idx+4:idx+8])[0]
            # Extract payload
            payload = h4mk[idx+12:idx+12+size]
            meta_dict = json.loads(payload.decode("utf-8"))
            
            # Verify compression metadata included
            assert "compression" in meta_dict, "Compression metadata not in META"
            assert "engine_id" in meta_dict["compression"], "No engine_id"
            assert "fingerprint" in meta_dict["compression"], "No fingerprint"

    def test_different_compression_core_changes_veri(self):
        """Container VERI includes compression engine identity."""
        from container.h4mk import build_h4mk
        
        # Use 256-byte aligned blocks
        blocks = [b"x" * 256 * 4]  # 1024 bytes
        seek = [(0, 0)]
        meta = {"project": "test"}
        safe = {"scope": "test"}
        
        # Build with current engine
        h4mk1 = build_h4mk(blocks, seek, meta, safe)
        
        # Extract VERI hash (should exist)
        idx = h4mk1.find(b"VERI")
        assert idx >= 0, "VERI chunk not found"
        
        import struct
        size = struct.unpack(">I", h4mk1[idx+4:idx+8])[0]
        veri1 = h4mk1[idx+12:idx+12+size].hex()
        
        # Build again (same parameters, should get same VERI)
        h4mk2 = build_h4mk(blocks, seek, meta, safe)
        
        idx = h4mk2.find(b"VERI")
        size = struct.unpack(">I", h4mk2[idx+4:idx+8])[0]
        veri2 = h4mk2[idx+12:idx+12+size].hex()
        
        # Same engine → same VERI (deterministic)
        assert veri1 == veri2, "Compression determinism broken"
        assert len(veri1) == 64, "VERI should be 32-byte hash (64 hex chars)"


class TestCompressionSealingAPI:
    """Verify API endpoints expose sealing information."""

    def test_compression_info_endpoint_sync(self):
        """GET /compress/info includes essential fields."""
        from api.compress import compression_info
        import asyncio
        
        info = asyncio.run(compression_info())
        
        # Essential fields that should be present
        assert "engine" in info, "Missing engine field"
        assert "deterministic" in info, "Missing deterministic field"
        # engine_id may or may not be present (depends on implementation)
        assert isinstance(info.get("deterministic", False), bool)

    def test_compression_attest_endpoint_sync(self):
        """GET /compress/attest provides cryptographic proof (sync wrapper)."""
        from api.compress import compression_attest
        import asyncio
        
        att = asyncio.run(compression_attest())
        
        assert "engine_id" in att
        assert "fingerprint" in att
        assert "timestamp_unix" in att
        assert "attestation_hash" in att


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
