"""HarmonyØ4 Audio API: FFT Streaming + Transport Masking

/audio/stream  → SSE harmonic bin tokens (real FFT, not identity)
/audio/mask    → Apply XOR mask to raw audio blocks
"""

from __future__ import annotations
from fastapi import APIRouter, UploadFile, Query
from fastapi.responses import StreamingResponse, Response
import json
from typing import Optional

from tokenizers.audio_fft import AudioFFTTokenizer
from utils.crypto import MaskSpec, derive_block_key, xor_mask

router = APIRouter(prefix="/audio", tags=["audio"])


def _sse(event: str, data_obj) -> bytes:
    """Encode Server-Sent Event."""
    data = json.dumps(data_obj, separators=(",", ":"), ensure_ascii=False)
    return f"event:{event}\ndata:{data}\n\n".encode("utf-8")


@router.post("/stream", summary="Stream Audio Tokens (FFT Harmonics)")
async def stream_audio_tokens(
    file: UploadFile,
    sample_rate: int = Query(48000, ge=8000, le=192000),
    frame_size: int = Query(2048, ge=256, le=16384),
    top_k: int = Query(32, ge=1, le=256),
):
    """Stream audio FFT harmonic bins as Server-Sent Events.
    
    Real FFT tokenization: structure-first, not identity-preserving.
    Top-K magnitude bins per frame, normalized [0, 1].
    
    Args:
        file: PCM16LE mono audio file
        sample_rate: Sample rate (Hz)
        frame_size: FFT window size (power of 2)
        top_k: Number of highest-magnitude bins per frame
    
    Yields:
        SSE events:
          - "meta": tokenizer config
          - "token": AudioToken (bin_hz, magnitude, phase, hex)
          - "done": completion marker
    """
    pcm = await file.read()
    tok = AudioFFTTokenizer(
        sample_rate=sample_rate, frame_size=frame_size, top_k=top_k
    )

    async def gen():
        yield _sse(
            "meta",
            {"sample_rate": sample_rate, "frame_size": frame_size, "top_k": top_k},
        )
        for t in tok.encode_pcm16le_mono(pcm):
            yield _sse(
                "token",
                {
                    "bin_hz": round(t.bin_hz, 1),
                    "magnitude": round(t.magnitude, 4),
                    "phase": round(t.phase, 4),
                    "token_hex": t.serialize().hex(),
                },
            )
        yield _sse("done", {"ok": True, "project": "HarmonyØ4"})

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.post("/mask", summary="Apply XOR Mask to Audio Transport Blocks")
async def mask_audio_transport(
    file: UploadFile,
    block_size: int = Query(
        256 * 1024, ge=16 * 1024, le=4 * 1024 * 1024
    ),
    master_key_hex: str = Query(
        ..., description="Master key: 64 hex chars for 32 bytes"
    ),
):
    """Apply per-block XOR mask to audio transport blocks.
    
    Transport-only masking via HKDF-derived keystream (SHA256-based).
    No codec semantics. No identity. Pure structural masking.
    
    Args:
        file: Raw audio blocks
        block_size: Bytes per block
        master_key_hex: Master key (64 hex chars = 32 bytes)
    
    Returns:
        Masked audio blocks (same structure, XOR'ed with keystream)
    """
    raw = await file.read()
    blocks = [raw[i : i + block_size] for i in range(0, len(raw), block_size)]

    # Parse master key
    try:
        master_key = bytes.fromhex(master_key_hex)
    except ValueError:
        return Response("master_key_hex must be valid hex.", status_code=400)

    if len(master_key) < 16:
        return Response("master_key must be at least 16 bytes.", status_code=400)

    spec = MaskSpec(enabled=True)

    # Mask each block
    out = bytearray()
    for i, b in enumerate(blocks):
        key = derive_block_key(master_key, i, spec)
        out += xor_mask(b, key)

    return Response(
        content=bytes(out),
        media_type="application/octet-stream",
        headers={"Content-Disposition": 'attachment; filename="HarmonyØ4_audio.masked"'},
    )
