"""HarmonyØ4 Crypto Module Tests

Tests for HKDF key derivation and XOR masking.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.crypto import sha256, derive_block_key, xor_mask, MaskSpec


def test_sha256():
    """SHA256 hash function."""
    data = b"test data"
    result = sha256(data)
    assert len(result) == 32
    assert isinstance(result, bytes)


def test_mask_spec():
    """MaskSpec configuration."""
    spec = MaskSpec(enabled=True)
    assert spec.enabled is True
    assert spec.context == b"Harmony\xc3\x984|Mask|v1"
    assert spec.length == 32


def test_hkdf_derivation():
    """HKDF per-block key derivation."""
    master_key = sha256(b"test-master-key")
    spec = MaskSpec(enabled=True)
    
    # Different blocks should have different keys
    key0 = derive_block_key(master_key, 0, spec)
    key1 = derive_block_key(master_key, 1, spec)
    
    assert len(key0) == 32
    assert len(key1) == 32
    assert key0 != key1  # Different block indices


def test_xor_mask_reversibility():
    """XOR mask is reversible."""
    test_data = b"Hello, HarmonyO4!" * 10
    key = sha256(b"test-key")
    
    masked = xor_mask(test_data, key)
    unmasked = xor_mask(masked, key)
    
    assert unmasked == test_data
    assert masked != test_data


def test_xor_mask_deterministic():
    """XOR masking is deterministic."""
    test_data = b"Test" * 100
    key = sha256(b"same-key")
    
    masked1 = xor_mask(test_data, key)
    masked2 = xor_mask(test_data, key)
    
    assert masked1 == masked2


if __name__ == "__main__":
    test_sha256()
    test_mask_spec()
    test_hkdf_derivation()
    test_xor_mask_reversibility()
    test_xor_mask_deterministic()
    print("✅ All crypto tests passed")
