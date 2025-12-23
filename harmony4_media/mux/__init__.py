# harmony4_media/mux/__init__.py
"""
H4MK Multiplex: container format + GOP routing.

Core exports:
  - mux/parse/extract: H4MK container I/O
  - make_flags/parse_flags: GOP timing + block type encoding
  - mux_multitrack_gop: multi-track builder
  - TrackSpec/Block: data classes
  - find_keyframe_for_time/get_decode_chain: decode logic
"""

from .h4mk import (
    mux,
    parse,
    extract,
    extract_json,
    list_chunks,
    Chunk,
    ChunkInfo,
    T_CORE,
    T_META,
    T_SAFE,
    T_VERI,
    T_NOTE,
    build_seek_table,
    parse_seek_table,
)

from .gop_flags import (
    make_flags,
    parse_flags,
    BLK_I,
    BLK_P,
    BLK_B,
    blk_type_str,
)

from .h4mk_multitrack import (
    TrackSpec,
    Block,
    mux_multitrack_gop,
    read_tracks,
    find_keyframe_for_time,
    get_decode_chain,
    pretty_list_core,
    wrap_core_payload,
    unwrap_core_payload,
)

__all__ = [
    # H4MK core
    "mux",
    "parse",
    "extract",
    "extract_json",
    "list_chunks",
    "Chunk",
    "ChunkInfo",
    "T_CORE",
    "T_META",
    "T_SAFE",
    "T_VERI",
    "T_NOTE",
    "build_seek_table",
    "parse_seek_table",
    # GOP flags
    "make_flags",
    "parse_flags",
    "BLK_I",
    "BLK_P",
    "BLK_B",
    "blk_type_str",
    # Multi-track
    "TrackSpec",
    "Block",
    "mux_multitrack_gop",
    "read_tracks",
    "find_keyframe_for_time",
    "get_decode_chain",
    "pretty_list_core",
    "wrap_core_payload",
    "unwrap_core_payload",
]
