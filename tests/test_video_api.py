#!/usr/bin/env python3
"""
tests/test_video_api.py

Integration test: video tokenization + seeking.
"""

import sys
from pathlib import Path

# Add repo to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tokenizers.video import VideoTokenizer, VideoBlockToken
from container import SeekTable, CoreChunk, ChunkStream


def test_video_tokenizer():
    """Test basic video tokenization."""
    print("\n[1] Video Tokenizer Test")
    print("-" * 50)

    # Create fake frame blocks
    frames = [b"FRAME_%d" % i for i in range(100)]

    tokenizer = VideoTokenizer(fps=30.0, gop_size=30)
    tokens = list(tokenizer.encode(frames))

    print(f"  ✓ Generated {len(tokens)} tokens")
    assert len(tokens) == 100, "Token count mismatch"

    # Check keyframes
    keyframes = [t for t in tokens if t.is_keyframe]
    print(f"  ✓ Keyframes: {len(keyframes)} (every 30 frames)")
    assert len(keyframes) == 4, "Expected 4 keyframes at indices 0, 30, 60, 90"

    # Check PTS progression
    for i, token in enumerate(tokens):
        expected_pts = i * (1_000_000 // 30)  # 33,333 us per frame @ 30fps
        assert token.pts == expected_pts, f"PTS mismatch at {i}"

    print("  ✓ PTS progression correct")
    return tokens


def test_seek_table():
    """Test binary search on seek table."""
    print("\n[2] Seek Table Test")
    print("-" * 50)

    tokens = test_video_tokenizer()

    # Build seek table from keyframes only
    seek = SeekTable()
    offset = 0
    for token in tokens:
        if token.is_keyframe:
            seek.add(token.pts, offset)
        offset += 7  # "FRAME_%d" is ~7 bytes

    seek.finalize()

    print(f"  ✓ Built seek table with {len(seek)} entries")
    assert len(seek) == 4, "Expected 4 keyframe entries"

    # Test seeking
    test_cases = [
        (0, 0),  # Start -> keyframe at 0
        (30000, 0),  # Before second keyframe -> keyframe at 0
        (33333 * 15, 0),  # Midway in first GOP -> nearest keyframe at 0
        (33333 * 30, 33333 * 30),  # At second keyframe
        (33333 * 60, 33333 * 60),  # At third keyframe
        (33333 * 90, 33333 * 90),  # At last keyframe
    ]

    for target_pts, expected_pts in test_cases:
        entry = seek.seek(target_pts)
        assert entry is not None, f"No entry found for {target_pts}"
        assert entry.pts == expected_pts, f"Seek mismatch: got {entry.pts}, expected {expected_pts}"
        print(f"  ✓ Seek({target_pts}us) -> {entry.pts}us @ offset {entry.offset}")


def test_token_serialization():
    """Test token round-trip."""
    print("\n[3] Token Serialization Test")
    print("-" * 50)

    # Create token
    original = VideoBlockToken(pts=12345678, block_index=42, is_keyframe=True)
    print(f"  Original: {original.metadata()}")

    # Serialize
    serialized = original.serialize()
    print(f"  Serialized: {len(serialized)} bytes, hex: {serialized.hex()[:32]}...")

    # Deserialize
    restored = VideoBlockToken.deserialize(serialized)
    print(f"  Restored: {restored.metadata()}")

    # Verify
    assert original.pts == restored.pts
    assert original.block_index == restored.block_index
    assert original.is_keyframe == restored.is_keyframe
    print("  ✓ Round-trip successful")


def test_chunk_stream():
    """Test chunk accumulation and filtering."""
    print("\n[4] Chunk Stream Test")
    print("-" * 50)

    stream = ChunkStream()

    # Add chunks for multiple tracks
    for track_id in [1, 2]:
        for frame_idx in range(10):
            chunk = CoreChunk(
                payload=b"FRAME" * 100,
                pts=frame_idx * 33333,
                is_keyframe=(frame_idx % 3 == 0),
                track_id=track_id,
            )
            stream.add(chunk)

    print(f"  ✓ Added {len(stream)} chunks ({stream.total_size()} bytes)")

    # Filter by track
    track1 = stream.by_track(1)
    print(f"  ✓ Track 1: {len(track1)} chunks")
    assert len(track1) == 10

    # Filter by time
    range_chunks = stream.by_time_range(0, 100000)
    print(f"  ✓ Time range [0, 100000us]: {len(range_chunks)} chunks")

    # Get keyframes
    keyframes = stream.keyframes()
    print(f"  ✓ Keyframes: {len(keyframes)} (every 3)")


def test_seek_table_serialization():
    """Test seek table round-trip."""
    print("\n[5] Seek Table Serialization Test")
    print("-" * 50)

    # Create and populate
    seek1 = SeekTable()
    for i in range(5):
        seek1.add(i * 1000, i * 10000)
    seek1.finalize()

    # Serialize
    serialized = seek1.serialize()
    print(f"  ✓ Serialized: {len(serialized)} bytes")

    # Deserialize
    seek2 = SeekTable.deserialize(serialized)
    print(f"  ✓ Deserialized: {len(seek2)} entries")

    # Verify
    assert len(seek1) == len(seek2)
    for e1, e2 in zip(seek1.entries, seek2.entries):
        assert e1.pts == e2.pts
        assert e1.offset == e2.offset

    print("  ✓ Round-trip successful")


def test_metadata_extraction():
    """Test extracting video metadata from tokens."""
    print("\n[6] Metadata Extraction Test")
    print("-" * 50)

    frames = [b"FRAME" for _ in range(150)]
    tokenizer = VideoTokenizer(fps=24.0, gop_size=30)
    tokens = list(tokenizer.encode(frames))

    metadata = tokenizer.decode(tokens)
    print(f"  Metadata:")
    for key, value in metadata.items():
        print(f"    {key}: {value}")

    assert metadata["frame_count"] == 150
    assert metadata["fps"] == 24.0
    assert metadata["keyframe_count"] == 5
    print("  ✓ Metadata extraction correct")


def main():
    print("\n" + "=" * 60)
    print("VIDEO API TEST SUITE")
    print("=" * 60)

    try:
        test_video_tokenizer()
        test_seek_table()
        test_token_serialization()
        test_chunk_stream()
        test_seek_table_serialization()
        test_metadata_extraction()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED ✓")
        print("=" * 60 + "\n")
        return 0
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
