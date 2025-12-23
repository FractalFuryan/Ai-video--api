"""
HTTP Range + SEEK Streaming Endpoints

Implements HTTP 206 Partial Content for range requests.
Uses H4MK container SEEK tables to enable byte-accurate seeking
in streaming scenarios (CDN-compatible).

Example:
    curl -H "Range: bytes=1000-2000" http://localhost:8000/video/range?h4mk=<hex>
"""

from fastapi import APIRouter, Header, Response, Query
from typing import Optional
import struct
from container.reader import H4MKReader

router = APIRouter(prefix="/video", tags=["video"])


def parse_range_header(range_header: str, total_size: int) -> tuple[int, int]:
    """
    Parse HTTP Range header and return (start, end) byte offsets.
    
    Supports:
    - "bytes=0-1000"      → (0, 1001)
    - "bytes=1000-"       → (1000, total_size)
    - "bytes=-500"        → (max(0, total_size-500), total_size)
    
    Args:
        range_header: Value of Range HTTP header
        total_size: Total size of resource in bytes
        
    Returns:
        (start, end) tuple where end is exclusive
    """
    if not range_header.startswith("bytes="):
        raise ValueError("Invalid Range header format")

    range_spec = range_header[6:]  # Remove "bytes="

    if "-" not in range_spec:
        raise ValueError("Invalid Range header format")

    parts = range_spec.split("-", 1)

    if parts[0] and parts[1]:
        # bytes=start-end
        start = int(parts[0])
        end = int(parts[1]) + 1
    elif parts[0]:
        # bytes=start-
        start = int(parts[0])
        end = total_size
    else:
        # bytes=-suffix
        suffix = int(parts[1])
        start = max(0, total_size - suffix)
        end = total_size

    # Validate
    if start >= total_size or start >= end:
        raise ValueError("Invalid range")

    return start, min(end, total_size)


@router.get("/range", response_class=Response)
async def range_stream(
    h4mk: str = Query(..., description="H4MK container as hex string"),
    range: Optional[str] = Header(default=None),
) -> Response:
    """
    Stream H4MK CORE data with HTTP Range support (206 Partial Content).
    
    Args:
        h4mk: H4MK container as hex-encoded string
        range: HTTP Range header (optional)
        
    Returns:
        - 200 OK: Full CORE payload if no Range header
        - 206 Partial Content: Requested byte range with Content-Range header
        - 416 Range Not Satisfiable: If range is invalid
        
    Example:
        # Full file
        GET /video/range?h4mk=48344d4b...
        
        # First 1KB
        GET /video/range?h4mk=48344d4b... -H "Range: bytes=0-1023"
        
        # Last 512 bytes
        GET /video/range?h4mk=48344d4b... -H "Range: bytes=-512"
    """
    try:
        # Decode hex container
        h4mk_data = bytes.fromhex(h4mk)
    except ValueError:
        return Response(content="Invalid hex encoding", status_code=400)

    try:
        reader = H4MKReader(h4mk_data)
    except ValueError as e:
        return Response(content=f"Invalid H4MK: {e}", status_code=400)

    # Get CORE payload
    core_chunks = reader.get_chunks(b"CORE")
    if not core_chunks:
        return Response(content="No CORE chunk", status_code=400)

    core_data = b"".join(core_chunks)
    total_size = len(core_data)

    # Handle Range header
    if not range:
        # Full file
        return Response(
            content=core_data,
            status_code=200,
            headers={"Accept-Ranges": "bytes"},
        )

    try:
        start, end = parse_range_header(range, total_size)
    except ValueError as e:
        return Response(
            content=f"Invalid range: {e}",
            status_code=416,
            headers={"Content-Range": f"bytes */{total_size}"},
        )

    # Partial content
    partial_data = core_data[start:end]
    return Response(
        content=partial_data,
        status_code=206,
        headers={
            "Content-Range": f"bytes {start}-{end-1}/{total_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(len(partial_data)),
        },
    )


@router.get("/seek", response_class=Response)
async def seek_lookup(
    h4mk: str = Query(..., description="H4MK container as hex string"),
    pts: int = Query(..., description="Target PTS in microseconds"),
) -> Response:
    """
    Binary search SEEK table to find keyframe at or before target PTS.
    
    Uses O(log n) algorithm on SEEK table.
    
    Args:
        h4mk: H4MK container as hex-encoded string
        pts: Target presentation timestamp in microseconds
        
    Returns:
        JSON with found keyframe entry: {pts, offset}
        or 404 if no keyframe found
        
    Example:
        GET /video/seek?h4mk=48344d4b...&pts=1000000
        
        Response:
        {
            "pts": 1000000,
            "offset": 12345,
            "message": "Keyframe at PTS 1000000us, offset 12345 bytes"
        }
    """
    try:
        h4mk_data = bytes.fromhex(h4mk)
    except ValueError:
        return Response(content="Invalid hex encoding", status_code=400)

    try:
        reader = H4MKReader(h4mk_data)
    except ValueError as e:
        return Response(content=f"Invalid H4MK: {e}", status_code=400)

    entry = reader.seek_to_pts(pts)
    if not entry:
        return Response(content="No keyframe found before that PTS", status_code=404)

    return Response(
        content=f'{{"pts": {entry.pts}, "offset": {entry.offset}, "message": '
        f'"Keyframe at PTS {entry.pts}us, offset {entry.offset} bytes"}}',
        status_code=200,
        media_type="application/json",
    )


@router.get("/info", response_class=Response)
async def container_info(
    h4mk: str = Query(..., description="H4MK container as hex string"),
) -> Response:
    """
    Inspect H4MK container structure and metadata.
    
    Args:
        h4mk: H4MK container as hex-encoded string
        
    Returns:
        JSON with chunk tags, sizes, metadata
        
    Example:
        GET /video/info?h4mk=48344d4b...
        
        Response:
        {
            "chunks": {
                "CORE": [{"offset": 32, "size": 10240, "crc": "abc12345"}],
                "SEEK": [{"offset": 10272, "size": 512, "crc": "def67890"}]
            },
            "metadata": {
                "duration_us": 1000000,
                "frame_count": 30
            },
            "integrity": true
        }
    """
    try:
        h4mk_data = bytes.fromhex(h4mk)
    except ValueError:
        return Response(content="Invalid hex encoding", status_code=400)

    try:
        reader = H4MKReader(h4mk_data)
    except ValueError as e:
        return Response(content=f"Invalid H4MK: {e}", status_code=400)

    # Build response
    chunks_info = {}
    for tag, chunks in reader.chunks.items():
        tag_str = tag.decode("utf-8", errors="ignore")
        chunks_info[tag_str] = [
            {"offset": c.offset, "size": c.size, "crc": f"{c.crc:08x}"}
            for c in chunks
        ]

    metadata = reader.get_metadata()
    integrity = reader.verify_integrity()

    response = {
        "chunks": chunks_info,
        "metadata": metadata,
        "integrity": integrity,
    }

    import json

    return Response(
        content=json.dumps(response, indent=2),
        status_code=200,
        media_type="application/json",
    )
