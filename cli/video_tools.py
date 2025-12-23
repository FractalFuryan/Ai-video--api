"""
CLI tools for HarmonyØ4 video transport.
"""

from __future__ import annotations
import argparse
import json
import base64
import sys

from container.reader import H4MKReader
from container.multitrack import unpack_seek_multi


def cmd_manifest(args):
    """Print manifest of H4MK video file."""
    data = open(args.file, "rb").read()
    r = H4MKReader(data)

    meta_chunks = r.get_chunks(b"META")
    if not meta_chunks:
        print("error: no META chunk", file=sys.stderr)
        return 1

    meta = json.loads(meta_chunks[0].decode("utf-8"))
    seekm_b64 = meta.get("seekm_b64", "")
    seekm = unpack_seek_multi(base64.b64decode(seekm_b64)) if seekm_b64 else {}

    print(json.dumps({
        "tracks": meta.get("tracks", []),
        "compression": meta.get("compression", {}),
        "seek_tracks": list(seekm.keys()),
        "core_blocks": len(r.get_chunks(b"CORE")),
    }, indent=2))
    return 0


def cmd_seek(args):
    """Seek to a keyframe in a specific track."""
    data = open(args.file, "rb").read()
    r = H4MKReader(data)

    meta_chunks = r.get_chunks(b"META")
    if not meta_chunks:
        print("error: no META chunk", file=sys.stderr)
        return 1

    meta = json.loads(meta_chunks[0].decode("utf-8"))
    seekm_b64 = meta.get("seekm_b64", "")
    seekm = unpack_seek_multi(base64.b64decode(seekm_b64)) if seekm_b64 else {}
    entries = seekm.get(args.track, [])

    if not entries:
        print(f"error: no seek entries for track '{args.track}'", file=sys.stderr)
        return 1

    chosen = entries[0]
    for e in entries:
        if e[0] <= args.pts_us:
            chosen = e
        else:
            break

    print(f"track={args.track} pts_us={args.pts_us} -> "
          f"keyframe_pts_us={chosen[0]} core_index={chosen[1]}")
    return 0


def cmd_block(args):
    """Fetch and save a CORE block."""
    data = open(args.file, "rb").read()
    r = H4MKReader(data)

    if args.raw:
        core = r.get_chunks(b"CORE")
        if args.index >= len(core):
            print(f"error: core_index {args.index} out of range", file=sys.stderr)
            return 1
        block = core[args.index]
        open(args.output or "block.bin", "wb").write(block)
        print(f"wrote {args.output or 'block.bin'} (raw CORE bytes, {len(block)} bytes)")
    else:
        blocks = list(r.iter_core_blocks(decompress=True))
        if args.index >= len(blocks):
            print(f"error: core_index {args.index} out of range", file=sys.stderr)
            return 1
        block = blocks[args.index]
        open(args.output or "block.bin", "wb").write(block)
        print(f"wrote {args.output or 'block.bin'} (decompressed, {len(block)} bytes)")

    return 0


def main():
    """Main CLI entry point."""
    p = argparse.ArgumentParser(
        prog="harmonyØ4-video",
        description="HarmonyØ4 video transport tools",
    )
    sub = p.add_subparsers(dest="cmd", required=True, help="command")

    # manifest
    man = sub.add_parser("manifest", help="print H4MK manifest")
    man.add_argument("file", help="H4MK video file")
    man.set_defaults(func=cmd_manifest)

    # seek
    seek = sub.add_parser("seek", help="seek to keyframe")
    seek.add_argument("file", help="H4MK video file")
    seek.add_argument("--track", required=True, help="track ID")
    seek.add_argument("--pts_us", type=int, required=True, help="target pts (microseconds)")
    seek.set_defaults(func=cmd_seek)

    # block
    blk = sub.add_parser("block", help="fetch CORE block")
    blk.add_argument("file", help="H4MK video file")
    blk.add_argument("--index", type=int, required=True, help="CORE block index")
    blk.add_argument("--raw", action="store_true", help="fetch raw CORE (no decompress)")
    blk.add_argument("--output", "-o", help="output filename (default: block.bin)")
    blk.set_defaults(func=cmd_block)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
