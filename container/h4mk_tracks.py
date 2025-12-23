"""
H4MK builder for multitrack video (uses existing build_h4mk).
Embeds SEEKM + TRAK in META for now (readable).
"""

from __future__ import annotations
from typing import List, Dict, Any
import base64

from container.h4mk import build_h4mk
from container.multitrack import TrackIndexEntry, pack_trak, build_seek_per_track, pack_seek_multi
from video.track import TrackBlock


def build_h4mk_tracks(
    blocks: List[TrackBlock],
    meta: Dict[str, Any],
    safe: Dict[str, Any],
) -> bytes:
    """
    Build H4MK container for multitrack video.
    
    - Packs blocks into CORE chunks (opaque)
    - Creates readable TRAK index (track_id, pts_us, kind, keyframe, core_index)
    - Creates readable SEEKM multi-track seek table
    - Stores SEEKM + TRAK as base64 in META (for compatibility)
    """
    core_blocks: List[bytes] = []
    trak_entries: List[TrackIndexEntry] = []

    for i, b in enumerate(blocks):
        core_blocks.append(b.payload)
        trak_entries.append(TrackIndexEntry(
            track_id=b.track_id,
            pts_us=b.pts_us,
            kind=b.kind,
            keyframe=b.keyframe,
            core_index=i,
        ))

    seek = build_seek_per_track(trak_entries)
    seekm = pack_seek_multi(seek)
    trak = pack_trak(trak_entries)

    meta2 = dict(meta)
    meta2["domain"] = "video-transport"
    meta2["tracks"] = sorted(list({b.track_id for b in blocks}))

    # Embed SEEKM + TRAK as base64 in META (safe, readable in JSON)
    meta2["seekm_b64"] = base64.b64encode(seekm).decode("ascii")
    meta2["trak_b64"] = base64.b64encode(trak).decode("ascii")

    # build_h4mk requires seek_entries param; we pass empty list since multi-track seek
    # is in META (readable). Global SEEK chunk can be empty or minimal.
    return build_h4mk(core_blocks=core_blocks, seek_entries=[], meta=meta2, safe=safe)
