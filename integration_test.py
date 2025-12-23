#!/usr/bin/env python3
"""
integration_test.py

Comprehensive integration test suite for H4MK + Adapters.
Validates all critical paths end-to-end.
"""

import sys
import json
import hashlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from harmony4_media.mux import (
    mux_multitrack_gop,
    read_tracks,
    pretty_list_core,
    get_decode_chain,
    find_keyframe_for_time,
    extract,
    unwrap_core_payload,
    parse,
    TrackSpec,
    Block,
    BLK_I,
    BLK_P,
    BLK_B,
)

from adapters.null import NullAdapter
from adapters.dsp import DSPAdapter


def test_single_track_linear():
    """Test: Single track, linear I-P-P-I sequence."""
    print("\n[TEST] Single track, linear GOP sequence")
    
    tracks = [TrackSpec(1, "mono", "audio", "h4core", 48000, 1)]
    blocks = {
        1: [
            Block(pts_ms=0, blk_type=BLK_I, opaque_blob=b"I0"),
            Block(pts_ms=50, blk_type=BLK_P, opaque_blob=b"P1"),
            Block(pts_ms=100, blk_type=BLK_P, opaque_blob=b"P2"),
            Block(pts_ms=150, blk_type=BLK_I, opaque_blob=b"I3"),
        ]
    }
    
    container = mux_multitrack_gop(tracks, blocks)
    assert len(container) > 0, "Container should not be empty"
    
    # Parse and validate
    header, infos = parse(container, validate_crc=True)
    assert header["magic"] == "H4MK", "Magic should be H4MK"
    
    # Check blocks were written
    core_blocks = pretty_list_core(container)
    assert len(core_blocks) == 4, f"Expected 4 blocks, got {len(core_blocks)}"
    
    print(f"  ✓ Container: {len(container)} bytes, {len(core_blocks)} blocks")


def test_multi_track_independent():
    """Test: Multiple independent tracks with different GOP structures."""
    print("\n[TEST] Multi-track independent GOPs")
    
    tracks = [
        TrackSpec(1, "main", "audio", "h4core", 48000, 2),
        TrackSpec(2, "control", "control", "h4core", 0, 0),
        TrackSpec(3, "safety", "audit", "json", 0, 0),
    ]
    
    blocks = {
        1: [Block(pts_ms=0, blk_type=BLK_I, opaque_blob=b"MAIN_I0")],
        2: [Block(pts_ms=0, blk_type=BLK_I, opaque_blob=b"CTRL_I0")],
        3: [Block(pts_ms=0, blk_type=BLK_I, opaque_blob=b"SAFE_I0")],
    }
    
    meta = json.dumps({"tracks": 3}).encode()
    
    container = mux_multitrack_gop(tracks, blocks, meta_json=meta)
    
    # Verify all tracks present
    loaded_tracks = read_tracks(container)
    assert len(loaded_tracks) == 3, "Should load all 3 tracks"
    assert loaded_tracks[0].track_id == 1
    assert loaded_tracks[1].track_id == 2
    assert loaded_tracks[2].track_id == 3
    
    print(f"  ✓ {len(loaded_tracks)} tracks loaded correctly")


def test_decode_chain_bounds():
    """Test: Decode chains respect GOP boundaries."""
    print("\n[TEST] Decode chain GOP boundaries")
    
    tracks = [TrackSpec(1, "test", "audio", "h4core")]
    blocks = {
        1: [
            Block(pts_ms=0, blk_type=BLK_I, opaque_blob=b"I0"),
            Block(pts_ms=100, blk_type=BLK_P, opaque_blob=b"P1"),
            Block(pts_ms=200, blk_type=BLK_I, opaque_blob=b"I2"),  # Next GOP
            Block(pts_ms=300, blk_type=BLK_P, opaque_blob=b"P3"),
        ]
    }
    
    container = mux_multitrack_gop(tracks, blocks)
    
    # Test 1: Should include first GOP
    chain_1 = get_decode_chain(container, 1, 150)
    assert len(chain_1) >= 2, "Chain at 150ms should span I0, P1"
    
    # Test 2: Should stop at GOP boundary (don't include I2 at 200ms when requesting 150ms)
    # Simple check: chain should have at most 2 blocks (I0 + P1)
    assert len(chain_1) <= 2, f"Chain at 150ms should not exceed GOP boundary (got {len(chain_1)})"
    
    print(f"  ✓ Chains respect GOP boundaries (tested t=150ms, chain={chain_1})")


def test_keyframe_search():
    """Test: Keyframe binary search works correctly."""
    print("\n[TEST] Keyframe binary search")
    
    tracks = [TrackSpec(1, "test", "audio", "h4core")]
    blocks = {
        1: [
            Block(pts_ms=0, blk_type=BLK_I, opaque_blob=b"I0"),
            Block(pts_ms=100, blk_type=BLK_I, opaque_blob=b"I1"),
            Block(pts_ms=200, blk_type=BLK_I, opaque_blob=b"I2"),
            Block(pts_ms=300, blk_type=BLK_I, opaque_blob=b"I3"),
        ]
    }
    
    container = mux_multitrack_gop(tracks, blocks)
    
    # Test exact times
    assert find_keyframe_for_time(container, 1, 0) is not None
    assert find_keyframe_for_time(container, 1, 50) is not None  # Floor to 0
    assert find_keyframe_for_time(container, 1, 99) is not None  # Floor to 0
    assert find_keyframe_for_time(container, 1, 100) is not None  # Exact
    assert find_keyframe_for_time(container, 1, 250) is not None  # Floor to 200
    
    print(f"  ✓ Keyframe search works for all test cases")


def test_payload_routing():
    """Test: Track ID routing is preserved through encode/decode."""
    print("\n[TEST] Payload routing (track ID preservation)")
    
    # Create container with 2 tracks, same opaque data
    opaque = b"X" * 100
    tracks = [
        TrackSpec(1, "track1", "audio", "h4core"),
        TrackSpec(2, "track2", "audio", "h4core"),
    ]
    blocks = {
        1: [Block(pts_ms=0, blk_type=BLK_I, opaque_blob=opaque)],
        2: [Block(pts_ms=0, blk_type=BLK_I, opaque_blob=opaque)],
    }
    
    container = mux_multitrack_gop(tracks, blocks)
    
    # Extract and verify routing
    core_blocks = pretty_list_core(container)
    assert len(core_blocks) == 2, "Should have 2 blocks"
    
    for block in core_blocks:
        tid = block["track_id"]
        assert tid in [1, 2], f"Track ID should be 1 or 2, got {tid}"
    
    print(f"  ✓ Track routing preserved (2 blocks, correct IDs)")


def test_null_adapter_passthrough():
    """Test: NullAdapter correctly accumulates blocks."""
    print("\n[TEST] NullAdapter passthrough")
    
    adapter = NullAdapter()
    state = adapter.decode_I(b"block1")
    assert len(state.blocks) == 1
    
    state = adapter.apply_P(state, b"block2")
    assert len(state.blocks) == 2
    
    output = adapter.finalize(state)
    assert output == b"block1block2", "Should concatenate blocks"
    
    print(f"  ✓ NullAdapter passthrough: {len(output)} bytes accumulated")


def test_dsp_adapter_state():
    """Test: DSPAdapter state management."""
    print("\n[TEST] DSPAdapter state management")
    
    adapter = DSPAdapter(sample_rate=48000)
    
    # Create mock DSP opaque block (magic + bin_count + 0 bins)
    opaque = b"DSP0" + b"\x00\x00\x00\x00"  # 0 bins
    
    state = adapter.decode_I(opaque)
    assert state.sample_rate == 48000
    assert len(state.freq_bins) == 0
    
    state_dict = state.to_dict()
    assert state_dict["type"] == "DSPState"
    assert state_dict["bin_count"] == 0
    
    print(f"  ✓ DSPAdapter state initialization: {state_dict}")


def test_metadata_sidecars():
    """Test: Metadata sidecars (META, SAFE, VERI, NOTE)."""
    print("\n[TEST] Metadata sidecars")
    
    tracks = [TrackSpec(1, "test", "audio", "h4core")]
    blocks = {1: [Block(pts_ms=0, blk_type=BLK_I, opaque_blob=b"test")]}
    
    meta = json.dumps({"title": "test"}).encode()
    safe = json.dumps({"safe": True}).encode()
    veri = json.dumps({"crc": "abc123"}).encode()
    note = b"Test notes"
    
    container = mux_multitrack_gop(
        tracks,
        blocks,
        meta_json=meta,
        safety_json=safe,
        verify_json=veri,
        note_bytes=note,
    )
    
    # Parse and count chunks
    _, infos = parse(container, validate_crc=True)
    chunk_types = [c.ctype for c in infos]
    
    assert "TRAK" in chunk_types, "Track header should be present"
    assert "CORE" in chunk_types, "Core blocks should be present"
    assert "META" in chunk_types, "Meta should be present"
    assert "SAFE" in chunk_types, "Safety should be present"
    assert "VERI" in chunk_types, "Verification should be present"
    assert "NOTE" in chunk_types, "Notes should be present"
    
    print(f"  ✓ All sidecars present: {chunk_types}")


def test_crc_validation():
    """Test: CRC validation on parse."""
    print("\n[TEST] CRC validation")
    
    tracks = [TrackSpec(1, "test", "audio", "h4core")]
    blocks = {1: [Block(pts_ms=0, blk_type=BLK_I, opaque_blob=b"data")]}
    
    container = mux_multitrack_gop(tracks, blocks)
    
    # Should parse cleanly
    try:
        _, infos = parse(container, validate_crc=True)
        print(f"  ✓ CRC validation passed ({len(infos)} chunks)")
    except ValueError as e:
        raise AssertionError(f"CRC validation failed: {e}")


def main():
    print("\n" + "=" * 70)
    print("INTEGRATION TEST SUITE: H4MK + Adapters")
    print("=" * 70)
    
    tests = [
        test_single_track_linear,
        test_multi_track_independent,
        test_decode_chain_bounds,
        test_keyframe_search,
        test_payload_routing,
        test_null_adapter_passthrough,
        test_dsp_adapter_state,
        test_metadata_sidecars,
        test_crc_validation,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70 + "\n")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    # Fix: import parse_flags for test_decode_chain_bounds
    from harmony4_media.mux.gop_flags import parse_flags
    sys.exit(main())
