"""
CLI Tool for HarmonyØ4

Command-line interface for H4MK inspection, seeking, and export.
Git-like subcommand pattern.

Usage:
    harmonyø4 inspect demo.h4mk
    harmonyø4 seek demo.h4mk 1000000
    harmonyø4 export video.raw -o out.h4mk
"""

import argparse
import sys
from pathlib import Path
from container.reader import H4MKReader


def cmd_inspect(args) -> int:
    """
    Inspect H4MK container structure.
    
    Shows:
    - Chunk tags and sizes
    - Metadata (duration, frame count)
    - Integrity status
    """
    path = Path(args.file)
    if not path.exists():
        print(f"Error: {path} not found", file=sys.stderr)
        return 1

    try:
        data = path.read_bytes()
        reader = H4MKReader(data)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"📦 HarmonyØ4 Container: {path.name}")
    print(f"   Size: {len(data) / 1024:.1f} KB")
    print()

    print("Chunks:")
    for tag, chunks in sorted(reader.chunks.items()):
        tag_str = tag.decode("utf-8", errors="ignore")
        total_size = sum(c.size for c in chunks)
        print(f"  {tag_str:4s}: {len(chunks):2d} chunk(s), {total_size:8d} bytes")
        for i, chunk in enumerate(chunks):
            print(
                f"         [{i}] offset={chunk.offset:8d} size={chunk.size:8d} "
                f"crc={chunk.crc:08x}"
            )

    meta = reader.get_metadata()
    if meta:
        print()
        print("Metadata:")
        if "duration_us" in meta:
            dur_s = meta["duration_us"] / 1_000_000
            print(f"  Duration: {dur_s:.2f}s ({meta['duration_us']} µs)")
        if "frame_count" in meta:
            print(f"  Frames: {meta['frame_count']}")

    print()
    integrity = reader.verify_integrity()
    status = "✅ PASS" if integrity else "❌ FAIL"
    print(f"Integrity: {status}")

    return 0


def cmd_seek(args) -> int:
    """
    Binary search SEEK table for PTS.
    
    Shows the keyframe at or before the given presentation timestamp.
    """
    path = Path(args.file)
    if not path.exists():
        print(f"Error: {path} not found", file=sys.stderr)
        return 1

    target_pts = args.pts
    if target_pts < 0:
        print("Error: PTS must be >= 0", file=sys.stderr)
        return 1

    try:
        data = path.read_bytes()
        reader = H4MKReader(data)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    seek_table = reader.get_seek_table()
    if not seek_table:
        print("Error: No SEEK table in container", file=sys.stderr)
        return 1

    entry = reader.seek_to_pts(target_pts)
    if not entry:
        print(
            f"No keyframe found at or before {target_pts} µs",
            file=sys.stderr,
        )
        return 1

    # Show result
    print(f"🎯 Seek to {target_pts} µs")
    print(f"   Found: PTS {entry.pts} µs @ offset {entry.offset} bytes")
    print()
    print("Full SEEK table:")
    for i, e in enumerate(seek_table):
        marker = " ← HERE" if e.pts == entry.pts else ""
        print(f"   [{i:3d}] {e.pts:12d} µs @ offset {e.offset:8d} B{marker}")

    return 0


def cmd_export(args) -> int:
    """
    Export (build) H4MK container from raw media.
    
    For demo purposes, wraps raw data into H4MK container.
    """
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        return 1

    output_path = Path(args.output) if args.output else input_path.with_suffix(".h4mk")

    try:
        raw_data = input_path.read_bytes()
    except IOError as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        return 1

    # Simple H4MK builder (demo)
    from container.h4mk import H4MKBuilder

    builder = H4MKBuilder()
    try:
        # Add raw data as CORE
        builder.add_chunk(b"CORE", raw_data)
        # Finalize (auto-computes hashes)
        container = builder.finalize()
    except Exception as e:
        print(f"Error building container: {e}", file=sys.stderr)
        return 1

    try:
        output_path.write_bytes(container)
    except IOError as e:
        print(f"Error writing output: {e}", file=sys.stderr)
        return 1

    print(f"✅ Exported to {output_path}")
    print(f"   Size: {len(container) / 1024:.1f} KB")

    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="harmonyø4",
        description="HarmonyØ4 Media API — Deterministic transport layer",
    )

    subparsers = parser.add_subparsers(dest="cmd", help="Command to run")

    # inspect subcommand
    inspect_parser = subparsers.add_parser("inspect", help="Inspect H4MK container")
    inspect_parser.add_argument("file", help="H4MK file to inspect")

    # seek subcommand
    seek_parser = subparsers.add_parser("seek", help="Seek to PTS in container")
    seek_parser.add_argument("file", help="H4MK file to seek in")
    seek_parser.add_argument(
        "pts", type=int, help="Target PTS in microseconds"
    )

    # export subcommand
    export_parser = subparsers.add_parser("export", help="Build H4MK container")
    export_parser.add_argument("input", help="Input raw media file")
    export_parser.add_argument(
        "-o", "--output", help="Output H4MK file (default: input.h4mk)"
    )

    args = parser.parse_args()

    # Dispatch
    if args.cmd == "inspect":
        return cmd_inspect(args)
    elif args.cmd == "seek":
        return cmd_seek(args)
    elif args.cmd == "export":
        return cmd_export(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
