"""
Video tracks API: manifest, seek, block fetch endpoints.
"""

from __future__ import annotations
from fastapi import APIRouter, UploadFile, Query
from fastapi.responses import JSONResponse, Response
import base64
import json

from container.reader import H4MKReader
from container.multitrack import unpack_seek_multi

router = APIRouter(prefix="/video", tags=["video-tracks"])


@router.post("/manifest")
async def video_manifest(file: UploadFile):
    """
    Get manifest for uploaded H4MK video file.
    Returns: container type, meta, tracks, seek table, trak index, core block count.
    """
    data = await file.read()
    r = H4MKReader(data)

    meta_chunks = r.get_chunks(b"META")
    safe_chunks = r.get_chunks(b"SAFE")
    
    if not meta_chunks or not safe_chunks:
        return JSONResponse({"error": "missing META or SAFE chunk"}, status_code=400)

    meta = json.loads(meta_chunks[0].decode("utf-8"))
    safe = json.loads(safe_chunks[0].decode("utf-8"))

    seekm_b64 = meta.get("seekm_b64", "")
    trak_b64 = meta.get("trak_b64", "")
    seekm = unpack_seek_multi(base64.b64decode(seekm_b64)) if seekm_b64 else {}
    trak = json.loads(base64.b64decode(trak_b64).decode("utf-8")) if trak_b64 else {}

    return JSONResponse({
        "container": "H4MK",
        "meta": {k: v for k, v in meta.items() if k not in ("seekm_b64", "trak_b64")},
        "tracks": meta.get("tracks", []),
        "seek": {
            tid: [{"pts_us": int(p), "core_index": int(i)} for (p, i) in arr]
            for tid, arr in seekm.items()
        },
        "trak": trak.get("trak", []),
        "safe": safe,
        "core_blocks": len(r.get_chunks(b"CORE")),
    })


@router.post("/seek_to_block")
async def seek_to_block(
    file: UploadFile,
    track_id: str = Query(...),
    pts_us: int = Query(..., ge=0),
):
    """
    Seek to a keyframe for a specific track at or before pts_us.
    Returns: keyframe pts_us and corresponding core_index.
    """
    data = await file.read()
    r = H4MKReader(data)
    
    meta_chunks = r.get_chunks(b"META")
    if not meta_chunks:
        return JSONResponse({"error": "missing META chunk"}, status_code=400)
    
    meta = json.loads(meta_chunks[0].decode("utf-8"))
    seekm_b64 = meta.get("seekm_b64", "")
    seekm = unpack_seek_multi(base64.b64decode(seekm_b64)) if seekm_b64 else {}
    entries = seekm.get(track_id, [])
    
    if not entries:
        return JSONResponse({
            "track_id": track_id,
            "pts_us": pts_us,
            "found": False,
        })

    # Find last entry with pts <= target
    chosen = entries[0]
    for e in entries:
        if e[0] <= pts_us:
            chosen = e
        else:
            break
    
    return JSONResponse({
        "track_id": track_id,
        "pts_us": int(pts_us),
        "keyframe_pts_us": int(chosen[0]),
        "core_index": int(chosen[1]),
        "found": True,
    })


@router.post("/block")
async def get_core_block(
    file: UploadFile,
    core_index: int = Query(..., ge=0),
    decompress: bool = Query(True),
):
    """
    Fetch a CORE block by index.
    If decompress=True, decompresses (if sealed); else returns raw CORE bytes.
    """
    data = await file.read()
    r = H4MKReader(data)
    core = r.get_chunks(b"CORE")
    
    if core_index >= len(core):
        return Response("core_index out of range", status_code=416)
    
    if not decompress:
        return Response(content=core[core_index], media_type="application/octet-stream")
    
    # transparent decompress
    blocks = list(r.iter_core_blocks(decompress=True))
    if core_index >= len(blocks):
        return Response("core_index out of range after decompress", status_code=416)
    
    block = blocks[core_index]
    return Response(content=block, media_type="application/octet-stream")
