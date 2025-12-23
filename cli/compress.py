"""HarmonyØ4 Compression CLI Tool

Compress/decompress files using reference or binary core engine.

Usage:
  harmonyø4-compress input.bin output.bin --mode compress
  harmonyø4-compress input.bin output.bin --mode decompress
"""

from __future__ import annotations
import argparse
import sys
from compression import load_engine


def main():
    """Main entry point for compression CLI."""
    parser = argparse.ArgumentParser(
        prog="harmonyø4-compress",
        description="HarmonyØ4 compression utility"
    )
    parser.add_argument("infile", help="Input file")
    parser.add_argument("outfile", help="Output file")
    parser.add_argument(
        "--mode",
        choices=["compress", "decompress"],
        default="compress",
        help="Operation mode (default: compress)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    try:
        # Load compression engine (reference or binary core)
        engine = load_engine()
        info = engine.info()

        if args.verbose:
            print(f"🔐 Engine: {info.get('engine', 'unknown')}", file=sys.stderr)
            print(f"   Deterministic: {info.get('deterministic', 'unknown')}", file=sys.stderr)
            print(f"   Identity-safe: {info.get('identity_safe', 'unknown')}", file=sys.stderr)
            print(f"   Open source: {info.get('open_source', 'unknown')}", file=sys.stderr)

        # Read input file
        with open(args.infile, "rb") as f:
            data = f.read()

        if args.verbose:
            print(f"📥 Read {len(data)} bytes from {args.infile}", file=sys.stderr)

        # Compress or decompress
        if args.mode == "compress":
            out = engine.compress(data)
            if args.verbose:
                ratio = 100.0 * len(out) / len(data) if data else 0
                print(f"   Compressed to {len(out)} bytes ({ratio:.1f}%)", file=sys.stderr)
        else:
            out = engine.decompress(data)
            if args.verbose:
                print(f"   Decompressed to {len(out)} bytes", file=sys.stderr)

        # Write output file
        with open(args.outfile, "wb") as f:
            f.write(out)

        if args.verbose:
            print(f"✅ Wrote {len(out)} bytes to {args.outfile}", file=sys.stderr)
        else:
            print(f"✅ OK ({args.mode}) engine={info.get('engine')} deterministic={info.get('deterministic')}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
