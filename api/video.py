"""HarmonyØ4 Video API: Streaming + H4MK Export

/video/stream  → SSE chunked tokens + metadata
/video/export  → H4MK container (CORE/META/SAFE/VERI/SEEK)
/video/export-encrypted → H4MK container with Living Cipher encryption
"""

from __future__ import annotations
from fastapi import APIRouter, UploadFile, Query
from fastapi.responses import StreamingResponse, Response
import json
from typing import Optional

from tokenizers.video_transport import VideoTransportTokenizer
from container.seek import SeekTable
from container.h4mk import build_h4mk
from utils.crypto import MaskSpec, derive_block_key, xor_mask, sha256
from crypto.living_cipher import init_from_shared_secret

router = APIRouter(prefix="/video", tags=["video"])


def _sse(event: str, data_obj) -> bytes:
    """Encode Server-Sent Event: event:type\ndata:json\n\n"""
    data = json.dumps(data_obj, separators=(",", ":"), ensure_ascii=False)
    return f"event:{event}\ndata:{data}\n\n".encode("utf-8")


@router.post("/stream", summary="Stream Video Tokens (SSE)")
async def stream_video_tokens(
    file: UploadFile,
    block_size: int = Query(512 * 1024, ge=64 * 1024, le=8 * 1024 * 1024),
    fps_hint: float = Query(30.0, ge=1.0, le=240.0),
    gop: int = Query(30, ge=1, le=600),
):
    """Stream video tokenization results as Server-Sent Events.
    
    Each block → one or more VideoBlockToken events.
    Useful for real-time progress, streaming decode chains.
    
    Args:
        file: Raw video file (opaque frames concatenated)
        block_size: Size of each logical block (bytes)
        fps_hint: Frames per second (for PTS calculation)
        gop: Keyframe interval (blocks between I-frames)
    
    Yields:
        SSE events:
          - "meta": tokenizer config
          - "token": VideoBlockToken (pts_us, block_index, is_key, hex)
          - "done": completion marker
    """
    raw = await file.read()
    blocks = [raw[i : i + block_size] for i in range(0, len(raw), block_size)]
    tok = VideoTransportTokenizer(fps_hint=fps_hint, gop=gop)

    async def gen():
        yield _sse(
            "meta",
            {
                "blocks": len(blocks),
                "block_size": block_size,
                "fps_hint": fps_hint,
                "gop": gop,
            },
        )
        for t in tok.encode_blocks(blocks):
            yield _sse(
                "token",
                {
                    "pts_us": t.pts_us,
                    "block_index": t.block_index,
                    "is_key": t.is_key,
                    "token_hex": t.serialize().hex(),
                },
            )
        yield _sse("done", {"ok": True, "project": "HarmonyØ4"})

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.post("/export", summary="Export Video as H4MK Container")
async def export_video_h4mk(
    file: UploadFile,
    block_size: int = Query(512 * 1024, ge=64 * 1024, le=8 * 1024 * 1024),
    fps_hint: float = Query(30.0, ge=1.0, le=240.0),
    gop: int = Query(30, ge=1, le=600),
    mask: bool = Query(False, description="Enable per-block XOR masking"),
    master_key_hex: Optional[str] = Query(
        None, description="Master key (64 hex chars = 32 bytes). Required if mask=true."
    ),
):
    """Export tokenized video to H4MK multi-track container.
    
    Container structure:
      - CORE chunks: opaque video blocks
      - SEEK table: (pts_us, offset) keyframe pairs for O(log n) seeking
      - META: tokenizer config + project metadata
      - SAFE: safety scopes (no synthesis, no pixel semantics)
      - VERI: SHA256 integrity hash of all prior chunks
    
    Args:
        file: Raw video file (opaque frames)
        block_size: Size of each logical block
        fps_hint: Frames per second
        gop: Keyframe interval
        mask: Enable XOR mask (transport-only, no codec leak)
        master_key_hex: Master key for mask derivation (if mask=true)
    
    Returns:
        H4MK binary file (application/octet-stream)
    """
    raw = await file.read()
    blocks = [raw[i : i + block_size] for i in range(0, len(raw), block_size)]

    # Validate and parse master key if masking enabled
    spec = MaskSpec(enabled=mask)
    master_key = None
    if mask:
        if not master_key_hex or len(master_key_hex) < 32:
            return Response(
                "mask=true requires master_key_hex (minimum 16 bytes, 32 hex chars).",
                status_code=400,
            )
        try:
            master_key = bytes.fromhex(master_key_hex)
        except ValueError:
            return Response("master_key_hex must be valid hex.", status_code=400)
        if len(master_key) < 16:
            return Response(
                "master_key_hex must represent at least 16 bytes.", status_code=400
            )

    # Tokenize and build container
    tok = VideoTransportTokenizer(fps_hint=fps_hint, gop=gop)
    seek = SeekTable()

    core_blocks = []
    offset = 0

    for t in tok.encode_blocks(blocks):
        payload = blocks[t.block_index]

        # Apply XOR mask if enabled
        if spec.enabled:
            key = derive_block_key(master_key, t.block_index, spec)
            payload = xor_mask(payload, key)

        core_blocks.append(payload)

        # Add keyframe to seek table
        if t.is_key:
            seek.add(t.pts_us, offset)

        offset += len(payload)

    seek.finalize()

    # Build metadata and safety scopes
    meta = {
        "project": "HarmonyØ4",
        "domain": "video-transport",
        "block_size": block_size,
        "fps_hint": fps_hint,
        "gop": gop,
        "masked": bool(spec.enabled),
    }
    safe = {
        "scope": "container+transport-only",
        "no_video_synthesis": True,
        "no_pixel_semantics": True,
        "no_visual_ml": True,
    }

    # Build H4MK container
    blob = build_h4mk(
        core_blocks=core_blocks, seek_entries=seek.entries, meta=meta, safe=safe
    )

    return Response(
        content=blob,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": 'attachment; filename="HarmonyØ4_video.h4mk"'
        },
    )


@router.post("/export-encrypted", summary="Export Video as Encrypted H4MK (Living Cipher v3)")
async def export_video_h4mk_encrypted(
    file: UploadFile,
    block_size: int = Query(512 * 1024, ge=64 * 1024, le=8 * 1024 * 1024),
    fps_hint: float = Query(30.0, ge=1.0, le=240.0),
    gop: int = Query(30, ge=1, le=600),
    shared_secret_hex: Optional[str] = Query(
        None, description="Shared secret (64 hex chars = 32 bytes) for Living Cipher initialization. If omitted, uses default."
    ),
    mask: bool = Query(False, description="Enable per-block XOR masking (optional, applied before encryption)"),
    master_key_hex: Optional[str] = Query(
        None, description="Master key for XOR mask (required if mask=true)"
    ),
):
    """Export tokenized video to encrypted H4MK container (Living Cipher v3).
    
    Pipeline: raw → compress → [XOR mask] → encrypt (LivingCipher) → CORE chunk
    
    Container structure:
      - CORE chunks: encrypted (Living Cipher v3) + compressed video blocks
      - SEEK table: (pts_us, offset) keyframe pairs for O(log n) seeking
      - META: tokenizer config + compression + encryption metadata
      - SAFE: safety scopes (no synthesis, no pixel semantics)
      - VERI: SHA256 integrity hash of all prior chunks
    
    Args:
        file: Raw video file (opaque frames)
        block_size: Size of each logical block
        fps_hint: Frames per second
        gop: Keyframe interval
        shared_secret_hex: Hex-encoded 32-byte shared secret for cipher init
        mask: Enable optional XOR masking before encryption
        master_key_hex: Key for XOR mask (required if mask=true)
    
    Returns:
        Encrypted H4MK binary file (application/octet-stream)
    """
    raw = await file.read()
    blocks = [raw[i : i + block_size] for i in range(0, len(raw), block_size)]

    # Parse and validate shared secret
    if shared_secret_hex:
        if len(shared_secret_hex) < 64:
            return Response(
                "shared_secret_hex must be 64 hex characters (32 bytes).",
                status_code=400,
            )
        try:
            shared_secret = bytes.fromhex(shared_secret_hex)
        except ValueError:
            return Response("shared_secret_hex must be valid hex.", status_code=400)
        if len(shared_secret) < 32:
            return Response("shared_secret_hex must represent at least 32 bytes.", status_code=400)
    else:
        # Default secret if none provided
        shared_secret = sha256(b"Harmony4_default_shared_secret")

    # Initialize cipher state
    try:
        cipher_state = init_from_shared_secret(shared_secret)
    except Exception as e:
        return Response(f"Failed to initialize cipher: {e}", status_code=400)

    # Validate and parse master key if masking enabled
    spec = MaskSpec(enabled=mask)
    master_key = None
    if mask:
        if not master_key_hex or len(master_key_hex) < 32:
            return Response(
                "mask=true requires master_key_hex (minimum 16 bytes, 32 hex chars).",
                status_code=400,
            )
        try:
            master_key = bytes.fromhex(master_key_hex)
        except ValueError:
            return Response("master_key_hex must be valid hex.", status_code=400)
        if len(master_key) < 16:
            return Response(
                "master_key_hex must represent at least 16 bytes.", status_code=400
            )

    # Tokenize and build container
    tok = VideoTransportTokenizer(fps_hint=fps_hint, gop=gop)
    seek = SeekTable()

    core_blocks = []
    offset = 0

    for t in tok.encode_blocks(blocks):
        payload = blocks[t.block_index]

        # Apply XOR mask if enabled (optional, before encryption)
        if spec.enabled:
            key = derive_block_key(master_key, t.block_index, spec)
            payload = xor_mask(payload, key)

        core_blocks.append(payload)

        # Add keyframe to seek table
        if t.is_key:
            seek.add(t.pts_us, offset)

        offset += len(payload)

    seek.finalize()

    # Build metadata and safety scopes
    meta = {
        "project": "HarmonyØ4",
        "domain": "video-transport",
        "block_size": block_size,
        "fps_hint": fps_hint,
        "gop": gop,
        "masked": bool(spec.enabled),
        "encrypted": True,
    }
    safe = {
        "scope": "container+transport-only",
        "no_video_synthesis": True,
        "no_pixel_semantics": True,
        "no_visual_ml": True,
    }

    # Build H4MK container WITH encryption
    blob = build_h4mk(
        core_blocks=core_blocks,
        seek_entries=seek.entries,
        meta=meta,
        safe=safe,
        cipher_state=cipher_state,  # ✅ ENABLE ENCRYPTION
    )

    return Response(
        content=blob,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": 'attachment; filename="HarmonyØ4_video_encrypted.h4mk"'
        },
    )
