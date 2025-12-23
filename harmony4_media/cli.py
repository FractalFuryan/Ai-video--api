#!/usr/bin/env python3
# harmony4_media/cli.py
"""
CLI for H4MK container manipulation.

Commands:
  mt_list:   list tracks and CORE blocks
  mt_chain:  compute decode chain for a time
  mt_build:  build a test container
"""

import argparse
import json
import sys
from typing import Optional

from harmony4_media.mux import (
    read_tracks,
    pretty_list_core,
    get_decode_chain,
    mux_multitrack_gop,
    TrackSpec,
    Block,
    BLK_I,
    BLK_P,
    BLK_B,
)


def cmd_mt_list(args):
    """List tracks and blocks in a container."""
    try:
        container = open(args.inp, "rb").read()
    except FileNotFoundError:
        print(f"Error: file not found: {args.inp}", file=sys.stderr)
        return 1

    try:
        tracks = read_tracks(container)
    except Exception as e:
        print(f"Error reading tracks: {e}", file=sys.stderr)
        return 1

    print("\n=== TRACKS ===")
    for t in tracks:
        print(f"  [{t.track_id}] {t.name}")
        print(f"      kind={t.kind}, codec={t.codec}")
        print(f"      {t.channels}ch @ {t.sample_rate}Hz")
        if t.note:
            print(f"      note: {t.note}")

    print("\n=== CORE BLOCKS ===")
    try:
        blocks = pretty_list_core(container)
    except Exception as e:
        print(f"Error reading blocks: {e}", file=sys.stderr)
        return 1

    for row in blocks:
        print(f"  [idx={row['chunk_index']}] "
              f"track={row['track_id']} "
              f"t={row['pts_ms']}ms "
              f"{row['blk']} "
              f"({row['opaque_bytes']}B)")

    return 0


def cmd_mt_chain(args):
    """Compute and display decode chain."""
    try:
        container = open(args.inp, "rb").read()
    except FileNotFoundError:
        print(f"Error: file not found: {args.inp}", file=sys.stderr)
        return 1

    try:
        chain = get_decode_chain(container, args.track, args.t_ms)
    except Exception as e:
        print(f"Error computing chain: {e}", file=sys.stderr)
        return 1

    print(f"Decode chain for track={args.track} t={args.t_ms}ms:")
    if not chain:
        print("  (empty)")
    else:
        for idx in chain:
            print(f"  -> chunk_index={idx}")

    return 0


def cmd_mt_build(args):
    """Build a test multi-track container."""
    tracks = [
        TrackSpec(
            track_id=1,
            name="main",
            kind="audio",
            codec="h4core",
            sample_rate=48000,
            channels=1,
            note="Primary audio track"
        ),
        TrackSpec(
            track_id=2,
            name="safety",
            kind="audit",
            codec="json",
            sample_rate=0,
            channels=0,
            note="Safety / audit track"
        ),
    ]

    # Mock opaque blobs (in real use, these come from your closed encoder)
    blocks_by_track = {
        1: [
            Block(pts_ms=0, blk_type=BLK_I, opaque_blob=b"I0_main_audio_keyframe_12345"),
            Block(pts_ms=33, blk_type=BLK_P, opaque_blob=b"P1_main_audio_predictive_67890"),
            Block(pts_ms=66, blk_type=BLK_B, opaque_blob=b"B2_main_audio_bidirectional_abc"),
            Block(pts_ms=99, blk_type=BLK_P, opaque_blob=b"P3_main_audio_predictive_def"),
            Block(pts_ms=333, blk_type=BLK_I, opaque_blob=b"I10_main_audio_keyframe_ghi"),
        ],
    }

    meta = json.dumps({"title": "H4MK Multi-Track Demo", "duration_ms": 333}).encode("utf-8")
    safety = json.dumps({"no_identity": True, "safe_for_demo": True}).encode("utf-8")

    try:
        container = mux_multitrack_gop(
            tracks,
            blocks_by_track,
            meta_json=meta,
            safety_json=safety,
        )
    except Exception as e:
        print(f"Error building container: {e}", file=sys.stderr)
        return 1

    # Write to file
    out_path = args.out or "demo_multitrack.h4mk"
    try:
        with open(out_path, "wb") as f:
            f.write(container)
        print(f"Wrote {len(container)} bytes to {out_path}")
        return 0
    except Exception as e:
        print(f"Error writing file: {e}", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="H4MK multi-track container CLI"
    )
    sub = parser.add_subparsers(dest="cmd", help="Command")

    # mt_list
    mt_list = sub.add_parser("mt_list", help="List tracks and blocks")
    mt_list.add_argument("--in", dest="inp", required=True, help="Input H4MK file")

    # mt_chain
    mt_chain = sub.add_parser("mt_chain", help="Compute decode chain")
    mt_chain.add_argument("--in", dest="inp", required=True, help="Input H4MK file")
    mt_chain.add_argument("--track", type=int, required=True, help="Track ID")
    mt_chain.add_argument("--t_ms", type=int, required=True, help="Target time (ms)")

    # mt_build
    mt_build = sub.add_parser("mt_build", help="Build test container")
    mt_build.add_argument("--out", default="demo_multitrack.h4mk", help="Output file")

    args = parser.parse_args()

    if args.cmd == "mt_list":
        return cmd_mt_list(args)
    elif args.cmd == "mt_chain":
        return cmd_mt_chain(args)
    elif args.cmd == "mt_build":
        return cmd_mt_build(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
