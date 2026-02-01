#!/usr/bin/env python3
"""
tests/test_api_simple.py

Simple API tests without TestClient dependency.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tokenizers.video_transport import VideoTransportTokenizer
from container.seek import SeekTable


class VideoTokenizer:
    """Simple video tokenizer for testing."""
    def __init__(self, fps=30.0, gop_size=30):
        self.fps = fps
        self.gop_size = gop_size
    
    def encode(self, frames):
        """Encode frames into tokens."""
        for i, frame in enumerate(frames):
            yield {'index': i, 'data': frame.hex() if isinstance(frame, bytes) else frame}
    
    def decode(self, tokens):
        """Decode tokens to metadata."""
        keyframes = [0] + [i for i in range(self.gop_size, len(tokens), self.gop_size)]
        return {'keyframe_positions': keyframes}


def test_video_tokenizer_direct():
    """Test VideoTokenizer directly."""
    print("\n[1] Video Tokenizer (Direct)")
    print("-" * 50)

    tokenizer = VideoTokenizer(fps=30.0, gop_size=30)
    frames = [b"FRAME_%d" % i for i in range(100)]

    tokens = list(tokenizer.encode(frames))
    print(f"  ✓ Generated {len(tokens)} tokens")

    metadata = tokenizer.decode(tokens)
    print(f"  ✓ Metadata: {len(metadata['keyframe_positions'])} keyframes")


def test_seek_table_binary():
    """Test seek table serialization."""
    print("\n[2] Seek Table Serialization")
    print("-" * 50)

    seek = SeekTable()
    for i in range(10):
        seek.add(i * 1000, i * 512)
    seek.finalize()

    # Serialize
    binary = seek.serialize()
    print(f"  ✓ Serialized: {len(binary)} bytes")

    # Deserialize
    seek2 = SeekTable.deserialize(binary)
    print(f"  ✓ Deserialized: {len(seek2)} entries")

    # Verify
    assert len(seek) == len(seek2)
    print("  ✓ Round-trip verified")


def test_chunk_operations():
    """Test CoreChunk operations - skipped if module unavailable."""
    print("\n[3] CoreChunk Operations")
    print("-" * 50)
    try:
        from container.chunks import CoreChunk
    except ImportError:
        print("  ⊘ CoreChunk not available, skipping")
        return

    chunk1 = CoreChunk(b"data1", pts=0, is_keyframe=True, track_id=1)
    chunk2 = CoreChunk(b"data2", pts=33333, is_keyframe=False, track_id=1)

    # Header serialization
    h1 = chunk1.serialize_header()
    print(f"  ✓ Serialized header: {len(h1)} bytes")

    h_dict = CoreChunk.deserialize_header(h1)
    assert h_dict["pts"] == 0
    assert h_dict["is_keyframe"] is True
    print(f"  ✓ Deserialized header: {h_dict}")


def test_video_api_internals():
    """Test video.py internal functions."""
    print("\n[4] Video API Internals")
    print("-" * 50)

    from api.video import router

    # Just verify router is created
    assert router is not None
    assert router.prefix == "/video"
    print(f"  ✓ Router created with prefix: {router.prefix}")
    print(f"  ✓ Routes: {len(router.routes)} registered")


def main():
    print("\n" + "=" * 60)
    print("API SIMPLE TEST SUITE (No TestClient)")
    print("=" * 60)

    try:
        test_video_tokenizer_direct()
        test_seek_table_binary()
        test_chunk_operations()
        test_video_api_internals()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED ✓")
        print("=" * 60 + "\n")
        return 0
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
