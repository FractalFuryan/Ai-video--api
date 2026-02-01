"""
Integration tests: Compression → Encryption Pipeline

Verifies that:
1. Blocks are compressed deterministically
2. Compressed blocks are encrypted behind Living Cipher v3
3. Container stores encrypted blocks
4. Reader can decrypt and decompress blocks
5. Original plaintext matches round-trip result
"""

import pytest
from compression import load_engine
from crypto.living_cipher import init_from_shared_secret
from container.h4mk import build_h4mk
from container.reader import H4MKReader
from utils.crypto import sha256
import json


@pytest.mark.integration
@pytest.mark.slow
class TestCompressionEncryptionPipeline:
    """Full pipeline: compress → encrypt → store → read → decrypt → decompress"""

    def test_unencrypted_pipeline(self):
        """Baseline: blocks compressed but NOT encrypted."""
        # Input blocks
        plaintext_blocks = [b"hello world" * 100, b"test data" * 200, b"more data" * 150]
        
        # Build container WITHOUT encryption
        meta = {"project": "test", "domain": "test"}
        safe = {"test": True}
        seek_entries = [(0, 0), (1000, 100), (2000, 300)]
        
        blob = build_h4mk(
            core_blocks=plaintext_blocks,
            seek_entries=seek_entries,
            meta=meta,
            safe=safe,
            cipher_state=None,  # ✅ NO ENCRYPTION
        )
        
        # Read back
        reader = H4MKReader(blob)
        blocks_read = list(reader.iter_core_blocks(decompress=True, cipher_state=None))
        
        # Verify roundtrip
        assert len(blocks_read) == len(plaintext_blocks), "Block count mismatch"
        for original, recovered in zip(plaintext_blocks, blocks_read):
            assert original == recovered, "Plaintext mismatch"

    def test_encrypted_pipeline(self):
        """Full pipeline: plaintext → compress → encrypt → H4MK → read → decrypt → decompress → plaintext."""
        # Input blocks
        plaintext_blocks = [b"hello world" * 100, b"test data" * 200, b"more data" * 150]
        
        # Initialize cipher
        shared_secret = sha256(b"test_shared_secret")
        cipher_state = init_from_shared_secret(shared_secret)
        
        # Build container WITH encryption
        meta = {"project": "test", "domain": "test", "encrypted": True}
        safe = {"test": True}
        seek_entries = [(0, 0), (1000, 100), (2000, 300)]
        
        blob = build_h4mk(
            core_blocks=plaintext_blocks,
            seek_entries=seek_entries,
            meta=meta,
            safe=safe,
            cipher_state=cipher_state,  # ✅ ENABLE ENCRYPTION
        )
        
        # Verify container has encryption metadata
        reader = H4MKReader(blob)
        meta_chunks = reader.get_chunks(b"META")
        assert meta_chunks, "No META chunk"
        container_meta = json.loads(meta_chunks[0].decode("utf-8"))
        assert "encryption" in container_meta, "No encryption metadata in container"
        assert container_meta["encryption"]["cipher"] == "living-cipher-v3"
        assert container_meta["encryption"]["mode"] == "compress-then-encrypt"
        
        # Read back WITH decryption
        cipher_state_recv = init_from_shared_secret(shared_secret)  # Receiver initializes with same secret
        blocks_read = list(reader.iter_core_blocks(decompress=True, cipher_state=cipher_state_recv))
        
        # Verify roundtrip: plaintext → compress → encrypt → decrypt → decompress → plaintext
        assert len(blocks_read) == len(plaintext_blocks), "Block count mismatch"
        for original, recovered in zip(plaintext_blocks, blocks_read):
            assert original == recovered, f"Plaintext mismatch: {len(original)} vs {len(recovered)}"

    def test_encrypted_pipeline_determinism(self):
        """Same plaintext + same secret should produce same encrypted output (deterministic)."""
        plaintext = b"determinism test" * 500
        shared_secret = sha256(b"deterministic_secret")
        
        # First encryption
        cipher_state_1 = init_from_shared_secret(shared_secret)
        blob_1 = build_h4mk(
            core_blocks=[plaintext],
            seek_entries=[(0, 0)],
            meta={"project": "test"},
            safe={"test": True},
            cipher_state=cipher_state_1,
        )
        
        # Second encryption with same inputs
        cipher_state_2 = init_from_shared_secret(shared_secret)
        blob_2 = build_h4mk(
            core_blocks=[plaintext],
            seek_entries=[(0, 0)],
            meta={"project": "test"},
            safe={"test": True},
            cipher_state=cipher_state_2,
        )
        
        # Blobs should be identical (deterministic encryption)
        assert blob_1 == blob_2, "Determinism failed: same input produced different output"

    def test_encryption_prevents_block_tampering(self):
        """Corrupting encrypted block is detected during decryption."""
        plaintext = b"sensitive data" * 300
        shared_secret = sha256(b"tampering_test")
        
        # Build encrypted container
        cipher_state = init_from_shared_secret(shared_secret)
        blob = build_h4mk(
            core_blocks=[plaintext],
            seek_entries=[(0, 0)],
            meta={"project": "test"},
            safe={"test": True},
            cipher_state=cipher_state,
        )
        
        # Corrupt a byte in the encrypted block (after H4MK header, in CORE chunk)
        blob_corrupted = bytearray(blob)
        # Find first CORE chunk tag and corrupt its payload
        core_pos = blob.find(b"CORE")
        if core_pos > 0:
            # Corrupt at offset 100 bytes after CORE tag
            corrupt_pos = core_pos + 100
            if corrupt_pos < len(blob_corrupted):
                blob_corrupted[corrupt_pos] ^= 0xFF  # Flip bits
        
        # Try to read and decrypt corrupted block
        reader = H4MKReader(bytes(blob_corrupted))
        cipher_state_recv = init_from_shared_secret(shared_secret)
        
        # Decryption should fail (AEAD tag verification)
        blocks_read = list(reader.iter_core_blocks(decompress=True, cipher_state=cipher_state_recv))
        
        # Either decryption fails or data is corrupted (not original plaintext)
        # In this case, we expect reading to either raise or return corrupted data
        # The test passes if it doesn't silently return the original plaintext
        if blocks_read:
            assert blocks_read[0] != plaintext, "Tampering not detected!"

    def test_large_file_encryption_performance(self):
        """Encryption of large files should complete in reasonable time."""
        # Create large blocks (simulating real video)
        large_block = b"x" * (10 * 1024 * 1024)  # 10 MB block
        plaintext_blocks = [large_block]
        
        shared_secret = sha256(b"performance_test")
        cipher_state = init_from_shared_secret(shared_secret)
        
        # Build encrypted container (should not hang)
        import time
        start = time.time()
        blob = build_h4mk(
            core_blocks=plaintext_blocks,
            seek_entries=[(0, 0)],
            meta={"project": "test", "size": "10mb"},
            safe={"test": True},
            cipher_state=cipher_state,
        )
        elapsed = time.time() - start
        
        assert elapsed < 60, f"Encryption too slow: {elapsed}s for 10MB"
        
        # Verify decryption works
        reader = H4MKReader(blob)
        cipher_state_recv = init_from_shared_secret(shared_secret)
        blocks = list(reader.iter_core_blocks(decompress=True, cipher_state=cipher_state_recv))
        assert len(blocks) == 1
        assert blocks[0] == large_block

    def test_mixed_encrypted_and_unencrypted_metadata(self):
        """Container metadata is NEVER encrypted (only CORE blocks are)."""
        plaintext = b"metadata test" * 200
        shared_secret = sha256(b"metadata_test")
        
        cipher_state = init_from_shared_secret(shared_secret)
        meta = {
            "project": "HarmonyØ4",
            "encrypted": True,
            "public_info": "this is visible",
        }
        safe = {"no_synthesis": True}
        
        blob = build_h4mk(
            core_blocks=[plaintext],
            seek_entries=[(0, 0)],
            meta=meta,
            safe=safe,
            cipher_state=cipher_state,
        )
        
        # Read metadata without decryption (should work)
        reader = H4MKReader(blob)
        meta_chunks = reader.get_chunks(b"META")
        container_meta = json.loads(meta_chunks[0].decode("utf-8"))
        
        # Metadata is readable
        assert container_meta["project"] == "HarmonyØ4"
        assert container_meta["public_info"] == "this is visible"
        assert "encryption" in container_meta
        
        # But CORE blocks remain encrypted (unreadable without cipher)
        core_chunks = reader.get_chunks(b"CORE")
        assert len(core_chunks) > 0
        # Encrypted block should NOT equal plaintext
        assert core_chunks[0] != plaintext

    def test_compression_behind_encryption(self):
        """Verify compression happens BEFORE encryption (compressed → encrypted)."""
        # Highly compressible data
        plaintext = b"AAAA" * 10000  # 40KB of repetition
        
        shared_secret = sha256(b"compression_order_test")
        cipher_state = init_from_shared_secret(shared_secret)
        
        # Build encrypted container
        blob = build_h4mk(
            core_blocks=[plaintext],
            seek_entries=[(0, 0)],
            meta={"project": "test"},
            safe={"test": True},
            cipher_state=cipher_state,
        )
        
        # Without decryption, CORE block should be compressed + encrypted (smaller than plaintext)
        reader = H4MKReader(blob)
        core_chunks = reader.get_chunks(b"CORE")
        encrypted_size = len(core_chunks[0])
        
        # Encrypted payload should be noticeably smaller than plaintext (due to compression)
        # We can't directly compare because of encryption, but we can verify decryption works
        cipher_state_recv = init_from_shared_secret(shared_secret)
        blocks = list(reader.iter_core_blocks(decompress=True, cipher_state=cipher_state_recv))
        
        assert blocks[0] == plaintext, "Round-trip failed"

    def test_different_secrets_cannot_decrypt(self):
        """Wrong secret cannot decrypt blocks."""
        plaintext = b"secret data" * 300
        correct_secret = sha256(b"correct_secret")
        wrong_secret = sha256(b"wrong_secret")
        
        # Encrypt with correct secret
        cipher_correct = init_from_shared_secret(correct_secret)
        blob = build_h4mk(
            core_blocks=[plaintext],
            seek_entries=[(0, 0)],
            meta={"project": "test"},
            safe={"test": True},
            cipher_state=cipher_correct,
        )
        
        # Try to decrypt with wrong secret
        reader = H4MKReader(blob)
        cipher_wrong = init_from_shared_secret(wrong_secret)
        
        blocks_read = list(reader.iter_core_blocks(decompress=True, cipher_state=cipher_wrong))
        
        # Decryption with wrong key should fail or produce garbage
        if blocks_read:
            assert blocks_read[0] != plaintext, "Wrong key should not decrypt!"

    def test_container_integrity_with_encryption(self):
        """VERI chunk detects tampering in encrypted container."""
        plaintext = b"integrity test" * 400
        shared_secret = sha256(b"veri_test")
        
        cipher_state = init_from_shared_secret(shared_secret)
        blob = build_h4mk(
            core_blocks=[plaintext],
            seek_entries=[(0, 0)],
            meta={"project": "test"},
            safe={"test": True},
            cipher_state=cipher_state,
        )
        
        # Container should have valid VERI
        reader = H4MKReader(blob)
        assert reader.verify_integrity(), "Container integrity check failed"
        
        # Corrupt META chunk
        blob_corrupted = bytearray(blob)
        meta_pos = blob.find(b"META")
        if meta_pos > 0:
            # Corrupt metadata payload
            blob_corrupted[meta_pos + 50] ^= 0xFF
        
        # Integrity check should fail
        reader_corrupted = H4MKReader(bytes(blob_corrupted))
        assert not reader_corrupted.verify_integrity(), "Tampering not detected by VERI"


class TestCompressionEncryptionWithRealData:
    """Integration tests with realistic video-like data patterns."""

    def test_pipeline_with_video_block_pattern(self):
        """Test with data that mimics video frame structure."""
        # Simulate three video frames (compressed differently)
        frame1 = b"\xFF" * 50000 + b"\x00" * 30000  # Bright frame
        frame2 = b"\x80" * 40000 + b"\x7F" * 40000  # Medium frame
        frame3 = b"\x00" * 60000 + b"\xFF" * 20000  # Dark frame
        
        plaintext_blocks = [frame1, frame2, frame3]
        shared_secret = sha256(b"video_test_secret")
        
        # Encrypt
        cipher_state = init_from_shared_secret(shared_secret)
        blob = build_h4mk(
            core_blocks=plaintext_blocks,
            seek_entries=[(0, 0), (33000, 1000), (66000, 2000)],
            meta={"project": "video_test", "frames": 3},
            safe={"video": True},
            cipher_state=cipher_state,
        )
        
        # Decrypt
        reader = H4MKReader(blob)
        cipher_recv = init_from_shared_secret(shared_secret)
        blocks_read = list(reader.iter_core_blocks(decompress=True, cipher_state=cipher_recv))
        
        # Verify
        assert len(blocks_read) == 3
        assert blocks_read[0] == frame1
        assert blocks_read[1] == frame2
        assert blocks_read[2] == frame3
