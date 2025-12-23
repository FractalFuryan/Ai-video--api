# api/audio.py
"""
Audio API: token extraction + seeking.

Endpoints:
  POST /audio/tokenize - Extract tokens from audio
  GET /audio/seek - Seek to time offset
  GET /audio/metadata - Audio metadata

Template structure (mirrors video.py for consistency).
"""

from fastapi import APIRouter, UploadFile, File, Query
from pydantic import BaseModel


router = APIRouter(prefix="/audio", tags=["audio"])


class AudioTokenizeResponse(BaseModel):
    """Audio tokenization response."""

    sample_count: int
    duration_sec: float
    tokens_count: int
    sample_rate: int


@router.post("/tokenize", response_model=AudioTokenizeResponse)
async def tokenize_audio(
    file: UploadFile = File(...),
    sample_rate: int = Query(48000, description="Sample rate (Hz)"),
):
    """
    Tokenize audio data.

    Args:
        file: Raw audio bytes (WAV, raw, etc).
        sample_rate: Audio sample rate.

    Returns:
        Token and timing information.
    """
    # Placeholder: actual audio tokenization would go here
    raw_data = await file.read()
    sample_count = len(raw_data) // 2  # assuming 16-bit samples
    duration_sec = sample_count / sample_rate

    return AudioTokenizeResponse(
        sample_count=sample_count,
        duration_sec=duration_sec,
        tokens_count=0,  # depends on tokenizer
        sample_rate=sample_rate,
    )


@router.get("/metadata")
async def get_audio_metadata(
    sample_rate: int = Query(48000),
):
    """Get audio format metadata."""
    return {
        "sample_rate": sample_rate,
        "api_version": "0.1.0",
    }
