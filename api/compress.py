"""HarmonyØ4 Compression API Endpoints

POST /compress — compress uploaded binary
POST /compress/decompress — decompress uploaded binary
GET /compress/info — compression engine metadata + attestation
GET /compress/attest — runtime engine attestation

All operations deterministic + verifiable.
All sealing information safely exposed.
"""

from __future__ import annotations
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import Response, JSONResponse
from compression import load_engine, attest, verify_attestation

router = APIRouter(prefix="/compress", tags=["compress"])


@router.get("/info")
async def compression_info():
    """
    Get compression engine metadata (no secrets).
    
    Includes:
    - engine: "core" or "reference"
    - engine_id: Version (e.g., "h4core-geo-v1.2.3")
    - fingerprint: SHA256 of core binary
    - deterministic: Always True
    - identity_safe: Always True
    - sealed: Whether verification passed
    
    Returns:
        JSON with engine name, determinism flag, identity_safe flag, etc.
    """
    engine = load_engine()
    return engine.info()


@router.get("/attest")
async def compression_attest():
    """
    Get runtime attestation of compression engine.
    
    Proves which engine is currently active:
    - engine_id: Public identifier
    - fingerprint: SHA256 proof
    - timestamp_unix: Freshness
    - attestation_hash: Cryptographic proof
    - sealed: Whether verification passed
    
    Safe to publish. No secrets disclosed.
    
    Returns:
        Attestation dict proving current engine state
    """
    return attest()


@router.post("")
async def compress_blob(file: UploadFile = File(...)):
    """
    Compress uploaded file using active engine.
    
    Args:
        file: Binary file to compress
        
    Returns:
        Compressed binary data
    """
    try:
        data = await file.read()
        engine = load_engine()
        compressed = engine.compress(data)
        
        return Response(
            content=compressed,
            media_type="application/octet-stream",
            headers={"X-Compressed-Size": str(len(compressed))}
        )
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )


@router.post("/decompress")
async def decompress_blob(file: UploadFile = File(...)):
    """
    Decompress uploaded file using active engine.
    
    Args:
        file: Compressed file to decompress
        
    Returns:
        Decompressed binary data
    """
    try:
        data = await file.read()
        engine = load_engine()
        decompressed = engine.decompress(data)
        
        return Response(
            content=decompressed,
            media_type="application/octet-stream",
            headers={"X-Decompressed-Size": str(len(decompressed))}
        )
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )
