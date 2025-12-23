# api/main.py
"""
Main FastAPI app: unified media API.

Mounts:
  - /video/*: frame tokenization + seeking
  - /audio/*: audio tokenization + seeking
  - /health: liveness probe

Philosophy:
  Clean separation: tokenization, seeking, transport
  No compression semantics in API layer
  Opaque data blocks only
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from api.video import router as video_router
from api.audio import router as audio_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle."""
    print("🎬 Media API starting...")
    yield
    print("🎬 Media API shutdown")


app = FastAPI(
    title="Harmony4 Media API",
    description="Unified video/audio tokenization + seeking",
    version="0.1.0",
    lifespan=lifespan,
)


# Mount routers
app.include_router(video_router)
app.include_router(audio_router)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return JSONResponse(
        {
            "status": "ok",
            "service": "harmony4-media-api",
            "version": "0.1.0",
        }
    )


@app.get("/")
async def root():
    """API root."""
    return {
        "name": "Harmony4 Media API",
        "description": "Container + tokenization for audio/video",
        "endpoints": {
            "health": "/health",
            "video": "/video/*",
            "audio": "/audio/*",
        },
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
