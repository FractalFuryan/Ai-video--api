"""HarmonyØ4 FastAPI Main Application

Unified media tokenization + seeking API.
Title enforced with Ø symbol for branding.
Includes Range + SEEK streaming for CDN-compatible delivery.
"""

from __future__ import annotations
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Import routers
from api.video import router as video_router
from api.audio import router as audio_router
from api.video_range import router as range_router
from api.compress import router as compress_router  # ✅ NEW
from api.video_compat import router as video_compat_router  # ✅ COMPATIBILITY


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown context."""
    print("✨ HarmonyØ4 Media API starting...")
    yield
    print("🌀 HarmonyØ4 shutting down...")


# Create app with HarmonyØ4 branding
app = FastAPI(
    title="HarmonyØ4 Media API",
    description="Transport-only media tokenization + seeking. Structure + timing only.",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount routers
app.include_router(video_router)
app.include_router(audio_router)
app.include_router(range_router)
app.include_router(compress_router)  # ✅ NEW
app.include_router(video_compat_router)  # ✅ COMPATIBILITY


@app.get("/", tags=["health"])
async def root():
    """Root endpoint listing all available endpoints."""
    return {
        "project": "HarmonyØ4",
        "status": "ready",
        "version": "1.0.0",
        "endpoints": {
            "video": [
                "/video/stream (SSE streaming)",
                "/video/export (H4MK container)",
                "/video/range (HTTP 206 range)",
                "/video/seek (SEEK table lookup)",
                "/video/info (container inspection)",
                "/video/manifest (player-friendly metadata)",
                "/video/block/{index} (random-access block fetch)",
                "/video/seek_to_block (timestamp → block mapping)",
                "/video/verify_integrity (VERI chunk check)",
            ],
            "audio": [
                "/audio/stream (SSE FFT)",
                "/audio/mask (transport encryption)",
            ],
            "compress": [
                "/compress (compress blob)",
                "/compress/decompress (decompress blob)",
                "/compress/info (engine metadata)",
            ],
            "health": ["/health"],
        },
    }


@app.get("/health", tags=["health"])
async def health():
    """Liveness probe."""
    return {"status": "healthy", "service": "HarmonyØ4"}


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "project": "HarmonyØ4"}
