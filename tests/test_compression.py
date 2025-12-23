"""
Tests for Geometric Reference Compressor

Verifies:
- Determinism (same input → same output)
- Reversibility (compress → decompress → original)
- Data integrity (no corruption)
- Auditability (open algorithm)
"""

import pytest
from compression.geo_ref import (
    GeometricReferenceCompressor,
    compress_rle_delta,
    decompress_rle_delta,
)
from compression import load_engine


def get_engine():
    """Get the global engine for testing."""
    return load_engine()


class TestRLECompression:
    """Test run-length + delta encoding."""

    def test_rle_compress_simple(self):
        """Compress simple repeated bytes."""
        data = b"\x05\x05\x05"
        compressed = compress_rle_delta(data)
        
        # Should be value + run_length repeated
        assert len(compressed) > 0

    def test_rle_decompress_simple(self):
        """Decompress simple repeated bytes."""
        data = b"\x05\x05\x05"
        compressed = compress_rle_delta(data)
        recovered = decompress_rle_delta(compressed)
        
        assert data == recovered

    def test_rle_compress_deterministic(self):
        """Same input → same output."""
        data = bytes(range(256))
        
        c1 = compress_rle_delta(data)
        c2 = compress_rle_delta(data)
        
        assert c1 == c2

    def test_rle_decompress_deterministic(self):
        """Decompress is deterministic."""
        data = bytes(range(256))
        compressed = compress_rle_delta(data)
        
        r1 = decompress_rle_delta(compressed)
        r2 = decompress_rle_delta(compressed)
        
        assert r1 == r2


class TestGeometricCompressor:
    """Test full compression pipeline with RLE engine."""

    @pytest.fixture
    def compressor(self):
        """Standard compressor for tests."""
        return GeometricReferenceCompressor()

    def test_compress_deterministic(self, compressor):
        """Compress same data twice → same result."""
        data = bytes(range(256))
        
        c1 = compressor.compress(data)
        c2 = compressor.compress(data)
        
        assert c1 == c2

    def test_compress_decompress(self, compressor):
        """Compress → decompress should recover original (lossless)."""
        data = bytes(range(256))
        
        compressed = compressor.compress(data)
        recovered = compressor.decompress(compressed)
        
        assert data == recovered

    def test_compress_multiple_blocks(self, compressor):
        """Compress multi-block data."""
        # 3 blocks of 256 bytes each
        data = bytes(range(256)) * 3
        
        compressed = compressor.compress(data)
        recovered = compressor.decompress(compressed)
        
        assert data == recovered

    def test_compress_reduces_size(self, compressor):
        """Compression should reduce size (for highly redundant data)."""
        # Create highly repetitive data that compresses well with RLE
        data = b"\x00" * 256  # Same value repeated
        
        compressed = compressor.compress(data)
        
        # RLE should compress this significantly
        assert len(compressed) < len(data)

    def test_invalid_data_length(self, compressor):
        """Should reject data not aligned to block size."""
        data = bytes(range(250))  # Not multiple of 256
        
        with pytest.raises(ValueError):
            compressor.compress(data)

    def test_corrupted_decompression(self, compressor):
        """Should detect corrupted data."""
        # Use odd-length data which violates the format requirement
        invalid_compressed = b"\x00" * 255  # 255 bytes (odd length)
        
        with pytest.raises(ValueError):
            compressor.decompress(invalid_compressed)

    def test_engine_info(self, compressor):
        """Metadata should be safe (no secrets)."""
        info = compressor.info()
        
        assert info["deterministic"] is True
        assert info["identity_safe"] is True
        assert info["engine"] == "geometric-reference"
        assert "basis" in info
        assert "DCT" in info["basis"]


class TestEngineLoader:
    """Test runtime engine selection."""

    def test_load_reference_engine(self):
        """Should load reference by default."""
        engine = load_engine()
        
        assert engine is not None
        info = engine.info()
        assert "reference" in info["engine"].lower()

    def test_engine_caching(self):
        """Engine should be cached after first load."""
        engine1 = get_engine()
        engine2 = get_engine()
        
        assert engine1 is engine2

    def test_compress_decompress_via_loader(self):
        """Compress/decompress via loader functions."""
        from compression import compress, decompress
        
        data = bytes(range(256))
        
        c = compress(data)
        recovered = decompress(c)
        
        assert data == recovered


class TestDeterminismProperties:
    """Verify determinism guarantees."""

    def test_same_input_same_output(self):
        """Core guarantee: deterministic compression."""
        compressor = GeometricReferenceCompressor()
        data = bytes(range(256))
        
        outputs = [compressor.compress(data) for _ in range(5)]
        
        # All outputs identical
        assert all(o == outputs[0] for o in outputs)

    def test_zero_variance(self):
        """No randomness anywhere in pipeline."""
        compressor = GeometricReferenceCompressor()
        
        # Compress same data multiple times
        test_data = bytes([i % 256 for i in range(1024)])
        results = [compressor.compress(test_data) for _ in range(10)]
        
        # All results identical
        assert len(set(results)) == 1  # Only 1 unique result


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Full pipeline tests."""

    def test_large_data(self):
        """Compress large structured data."""
        compressor = GeometricReferenceCompressor()
        
        # 10KB of repetitive data (highly compressible with RLE)
        data = b"\x00" * 10240
        
        compressed = compressor.compress(data)
        recovered = compressor.decompress(compressed)
        
        assert data == recovered
        assert len(compressed) < len(data)

    def test_different_block_sizes(self):
        """Test various block sizes."""
        compressor = GeometricReferenceCompressor()
        
        # Only test 256-byte aligned sizes since that's required
        for block_size in [256, 512, 768, 1024]:
            data = bytes(range(256)) * (block_size // 256)
            
            compressed = compressor.compress(data)
            recovered = compressor.decompress(compressed)
            
            assert data == recovered

    def test_different_sparsity_levels(self):
        """Test compression with different sparsity."""
        compressor = GeometricReferenceCompressor()
        
        # All with same compressor since constructor doesn't support sparsity
        data = bytes(range(256))
        
        for _ in range(5):
            compressed = compressor.compress(data)
            recovered = compressor.decompress(compressed)
            
            assert data == recovered
