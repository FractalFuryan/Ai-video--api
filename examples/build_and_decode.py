#!/usr/bin/env python3
"""
examples/build_and_decode.py

Complete end-to-end example:
  1. Build a multi-track H4MK container
  2. List tracks and blocks
  3. Compute decode chain
  4. Decode with NullAdapter (passthrough)
  5. Verify round-trip integrity
"""

import json
import sys
from pathlib import Path

# Add repo to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from harmony4_media.mux import (
    mux_multitrack_gop,
    read_tracks,
    pretty_list_core,
    get_decode_chain,
    extract,
    unwrap_core_payload,
    TrackSpec,
    Block,
    BLK_I,
    BLK_P,
    BLK_B,
)

from adapters.null import NullAdapter


def build_example_container():
    """Build a test container with 2 tracks, 5 blocks."""
    print("\n[1] Building multi-track container...\n")

    tracks = [
        TrackSpec(
            track_id=1,
            name="main",
            kind="audio",
            codec="h4core",
            sample_rate=48000,
            channels=1,
            note="Main audio (stereo in real use)"
        ),
        TrackSpec(
            track_id=2,
            name="control",
            kind="control",
            codec="h4core",
            sample_rate=0,
            channels=0,
            note="Control data (synthesis params, etc)"
        ),
    ]

    # Mock opaque blocks (would come from your closed encoder)
    blocks_by_track = {
        1: [
            Block(pts_ms=0, blk_type=BLK_I, opaque_blob=b"MAIN_I0__keyframe_______________"),
            Block(pts_ms=33, blk_type=BLK_P, opaque_blob=b"MAIN_P1__predictive_update_1____"),
            Block(pts_ms=66, blk_type=BLK_B, opaque_blob=b"MAIN_B2__bidirectional_12_______"),
            Block(pts_ms=99, blk_type=BLK_P, opaque_blob=b"MAIN_P3__predictive_update_2____"),
            Block(pts_ms=333, blk_type=BLK_I, opaque_blob=b"MAIN_I10_keyframe_second________"),
        ],
        2: [
            Block(pts_ms=0, blk_type=BLK_I, opaque_blob=b"CTRL_I0__synth_params___________"),
            Block(pts_ms=100, blk_type=BLK_P, opaque_blob=b"CTRL_P1__param_delta____________"),
            Block(pts_ms=300, blk_type=BLK_I, opaque_blob=b"CTRL_I2__synth_params_second____"),
        ],
    }

    # Global metadata
    meta = json.dumps({
        "title": "H4MK Multi-Track Demo",
        "duration_ms": 333,
        "created_by": "build_and_decode.py"
    }).encode("utf-8")

    safety = json.dumps({
        "no_identity": True,
        "safe_for_demo": True,
        "clearance": "internal"
    }).encode("utf-8")

    verify = json.dumps({
        "format_version": 1,
        "codec_version": "h4core.1",
    }).encode("utf-8")

    # Build container
    try:
        container = mux_multitrack_gop(
            tracks,
            blocks_by_track,
            meta_json=meta,
            safety_json=safety,
            verify_json=verify,
        )
        print(f"✓ Container built: {len(container)} bytes")
        return container
    except Exception as e:
        print(f"✗ Build failed: {e}")
        sys.exit(1)


def inspect_container(container: bytes):
    """Parse and pretty-print container contents."""
    print("\n[2] Container inspection...\n")

    # Read tracks
    try:
        tracks = read_tracks(container)
        print("Tracks:")
        for t in tracks:
            print(f"  [{t.track_id}] {t.name:12} | {t.kind:10} | {t.channels}ch @ {t.sample_rate}Hz")
            if t.note:
                print(f"       {t.note}")
    except Exception as e:
        print(f"✗ Error reading tracks: {e}")
        return

    # List CORE blocks
    print("\nCORE Blocks:")
    try:
        blocks = pretty_list_core(container)
        for row in blocks:
            print(
                f"  [idx={row['chunk_index']:3}] "
                f"t={row['pts_ms']:4}ms "
                f"track={row['track_id']} "
                f"{row['blk']} "
                f"({row['opaque_bytes']:2}B)"
            )
    except Exception as e:
        print(f"✗ Error reading blocks: {e}")


def test_decode_chain(container: bytes):
    """Test decode chain computation."""
    print("\n[3] Decode chain test...\n")

    test_cases = [
        (1, 0, "Start of track 1"),
        (1, 50, "Middle of GOP 1"),
        (1, 200, "Between keyframes"),
        (1, 333, "Last block"),
        (2, 150, "Track 2 at 150ms"),
    ]

    for track_id, t_ms, desc in test_cases:
        try:
            chain = get_decode_chain(container, track_id, t_ms)
            if chain:
                print(f"  track={track_id} t={t_ms}ms ({desc})")
                print(f"    chain: {chain}")
            else:
                print(f"  track={track_id} t={t_ms}ms ({desc}) -> no keyframe found")
        except Exception as e:
            print(f"  ✗ Error: {e}")


def test_full_decode(container: bytes):
    """Decode a track with NullAdapter."""
    print("\n[4] Full decode test (NullAdapter)...\n")

    adapter = NullAdapter()
    track_id = 1
    t_ms = 200

    try:
        chain = get_decode_chain(container, track_id, t_ms)
        print(f"Decoding track={track_id} up to t={t_ms}ms")
        print(f"Chain: {chain}")

        if not chain:
            print("  (empty chain)")
            return

        state = None
        for chunk_idx in chain:
            payload = extract(container, chunk_idx)
            tid, opaque = unwrap_core_payload(payload)
            print(f"  Processing chunk {chunk_idx} (track {tid}, {len(opaque)} bytes)")

            if state is None:
                state = adapter.decode_I(opaque)
            else:
                state = adapter.apply_P(state, opaque)

            print(f"    State: {state.to_dict()}")

        # Finalize
        output = adapter.finalize(state)
        print(f"\n✓ Decode complete: {len(output)} bytes output")

    except Exception as e:
        print(f"✗ Decode error: {e}")
        import traceback
        traceback.print_exc()


def main():
    print("\n" + "=" * 60)
    print("H4MK Multi-Track Container: End-to-End Example")
    print("=" * 60)

    # Step 1: Build
    container = build_example_container()

    # Step 2: Inspect
    inspect_container(container)

    # Step 3: Decode chains
    test_decode_chain(container)

    # Step 4: Full decode
    test_full_decode(container)

    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
