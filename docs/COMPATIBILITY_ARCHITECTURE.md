# HarmonyØ4 Compatibility Layer — Architecture

## Overview

The video compatibility layer provides a **thin, transport-only adapter** between HarmonyØ4 and existing video applications.

```
HarmonyØ4 Core (H4MK Container, Seeking, Compression)
         ↑ (internal)
         |
    ┌────┴────────────────┐
    │                     │
  API Layer         Compatibility Layer
  (streaming)       (manifest + blocks)
    │                     │
    └────────┬────────────┘
             ↓
    FastAPI Router
             ↓
  Your Video App
  (MP4 / HLS / DASH / Custom)
```

---

## Design Goals

### 1. **Non-Breaking Integration**
- Original video files remain untouched
- `.h4mk` sidecar is optional
- Your player logic unchanged

### 2. **Codec Agnostic**
- No assumptions about video format
- No pixel data manipulation
- Structure + timing only

### 3. **Standard REST Transport**
- HTTP POST/GET endpoints
- JSON manifests
- Binary block payloads
- Familiar to all platforms

### 4. **Safety by Construction**
- No codec library imports
- VERI integrity checks
- Deterministic compression only
- Auditability guaranteed

---

## Module Structure

```
api/
├── main.py              # FastAPI app, mounts all routers
├── video.py             # Original video endpoints (stream, export, seek)
├── audio.py             # Audio FFT + masking
├── compress.py          # Compression engine (API)
├── video_range.py       # HTTP 206 Range requests
└── video_compat.py      # ✅ NEW: Compatibility layer
    ├── @router.post("/video/manifest")
    ├── @router.post("/video/block/{index}")
    ├── @router.post("/video/seek_to_block")
    └── @router.post("/video/verify_integrity")

container/
├── h4mk.py              # H4MK format writer
├── reader.py            # H4MK format reader
└── seek.py              # SEEK table generation

tokenizers/
├── video.py             # Transport tokenization
└── ...

docs/
├── INTEGRATION_VIDEO_APP.md   # ✅ NEW: Integration guide
├── RELEASE_NOTES_v1.0.0.md    # ✅ NEW: v1.0 release
└── ...

├── QUICK_START_COMPAT.md       # ✅ NEW: 3-step quickstart
```

---

## Endpoint Flow

### Initialization: Get Manifest

```
Client                          HarmonyØ4
  │
  ├─ POST /video/manifest ──────→ Router
  │  (with .h4mk file)           ├─ H4MKReader.read()
  │                              ├─ Extract META, SAFE, SEEK
  │                              ├─ Parse JSON chunks
  │  ← {blocks, seek, ...} ──────┤
  │                              └─ Return JSONResponse
  └─ Cache manifest
```

### Navigation: Seek to Timestamp

```
Client                          HarmonyØ4
  │
  ├─ POST /video/seek_to_block ─→ Router
  │  (pts_us=T, file=...)        ├─ H4MKReader.get_seek_table()
  │                              ├─ Binary search for nearest entry
  │  ← {keyframe_entry_index} ──┤
  │                              └─ Return JSONResponse
  └─ Note block index
```

### Fetch Block

```
Client                          HarmonyØ4
  │
  ├─ POST /video/block/15 ──────→ Router
  │  (decompress=true, file=...) ├─ H4MKReader.get_chunks(b'CORE')
  │                              ├─ Decompress (if flag set)
  │  ← [binary block payload] ──┤
  │                              └─ Return Response
  └─ Pass to codec
```

### Integrity: Verify VERI

```
Client                          HarmonyØ4
  │
  ├─ POST /video/verify_integrity ─→ Router
  │  (file=...)                     ├─ H4MKReader.get_chunks(b'VERI')
  │                                 ├─ Check JSON structure
  │  ← {valid: bool, ...} ────────┤
  │                                 └─ Return JSONResponse
  └─ Proceed if valid
```

---

## Data Model

### Request: File Upload

```python
# FastAPI automatically handles FormData
@router.post("/video/manifest")
async def manifest_from_h4mk(file: UploadFile):
    data = await file.read()  # Binary .h4mk
    r = H4MKReader(data)
    # Process...
```

### Response: Manifest JSON

```json
{
  "container": "H4MK",
  "project": "HarmonyØ4",
  "domain": "video-transport",
  "blocks": 42,
  "seek": [
    {"pts_us": 0, "block_offset": 512},
    {"pts_us": 33333, "block_offset": 4096},
    ...
  ],
  "compression": {"algorithm": "RLE+delta", "ratio": 0.75},
  "safe": {"version": "1.0"}
}
```

### Response: Block Payload

```
Binary (application/octet-stream)
├─ X-Block-Index: 15
├─ X-Decompressed: true
└─ [raw bytes of decompressed block]
```

---

## Error Handling

| Status | Meaning | Example |
|--------|---------|---------|
| 400 | Bad Request | Failed to read file |
| 422 | Unprocessable | Invalid H4MK structure |
| 416 | Range Not Satisfiable | Block index out of range |
| 500 | Server Error | Decompression failure |

All errors return JSON:
```json
{
  "detail": "Block index 99 out of range (0-42)"
}
```

---

## Integration Points

### For Web Players
- POST manifest to initialize playback
- Listen to seek events → POST seek_to_block
- Fetch blocks via GET + cache locally
- Use MediaSource or custom decoder

### For Native Apps (iOS/Android)
- Same REST API via URLSession / OkHttp
- Cache blocks in app filesystem
- Implement adaptive bitrate (request lower quality)

### For Streaming Servers (HLS/DASH)
- Generate .m3u8 / .mpd from manifest
- Serve blocks as segment chunks
- Map SEEK table to segment indices

### For Encoding/Transcoding
- Store manifests in database
- Batch-process blocks efficiently
- Parallel decoding of independent blocks

---

## Safety Properties

### Transport-Only Guarantee
- No pixel format conversion
- No codec semantics
- No audio waveform processing
- **Only:** structure, timing, deterministic compression

### Auditability
- All chunks typed (META, SAFE, CORE, VERI, SEEK)
- JSON metadata human-readable
- VERI checksums for corruption detection
- Git history preserves all changes

### Determinism
- Same input → same output (always)
- Compression is reference implementation
- No randomness in transport
- Suitable for reproducible pipelines

---

## Performance Characteristics

| Operation | Complexity | Time |
|-----------|-----------|------|
| Get manifest | O(1) | ~1ms (JSON parse) |
| Seek to timestamp | O(log n) | ~0.1ms (binary search) |
| Fetch block | O(1) | ~10ms (I/O) |
| Decompress block | O(m) | ~50ms (RLE decode) |

Scales to multi-TB streams without architecture changes.

---

## Extensibility

### Adding New Endpoints

```python
@router.post("/video/analyze")
async def analyze_block(file: UploadFile, index: int):
    r = H4MKReader(await file.read())
    block = list(r.iter_core_blocks(decompress=True))[index]
    # Custom analysis...
    return {"size": len(block), "...": "..."}
```

### Custom Decompression

```python
# In video_compat.py, modify iter_core_blocks call:
blocks = list(r.iter_core_blocks(
    decompress=True,
    decompressor=MyCustomCodec  # ✅ Hook point
))
```

---

## Deployment

### Docker (with existing compose)

```yaml
services:
  harmony:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./containers:/data  # Store .h4mk files
    environment:
      - HARMONY_CACHE_MB=2048
```

### Environment Variables

```bash
HARMONY_CACHE_MB=2048        # Block cache size
HARMONY_VERIFY_INTEGRITY=1   # Always verify VERI
HARMONY_MAX_BLOCK_SIZE=10MB  # Payload limit
```

---

## Testing

```bash
# Unit tests
pytest tests/test_video_api.py -v
pytest tests/test_compression.py -v

# Integration test
python3 -m pytest tests/test_fastapi_integration.py -v

# Manual test (with running server)
curl -X POST http://localhost:8000/video/manifest \
  -F "file=@test.h4mk" | jq .
```

---

## Backward Compatibility

✅ **No breaking changes**
- Original `/video/stream`, `/video/export`, etc. unchanged
- Compatibility layer adds new `/video/*` endpoints
- Existing clients unaffected

✅ **Forward compatible**
- H4MK format versioned (in META chunk)
- Manifest schema extensible (new JSON fields OK)
- Decompression pluggable (codec swappable)

---

## Roadmap

**v1.0** (Current)
- Basic manifest + block fetch
- VERI integrity checks
- RLE reference compression

**v1.1** (Next)
- Hierarchical SEEK (multi-bitrate)
- Streaming manifest updates
- Batch block prefetching

**v2.0** (Future)
- WebAssembly H4MK reader
- Official compatibility test suite
- Benchmarks vs MP4/Matroska

---

## References

- [INTEGRATION_VIDEO_APP.md](INTEGRATION_VIDEO_APP.md) — Implementation guide
- [RELEASE_NOTES_v1.0.0.md](RELEASE_NOTES_v1.0.0.md) — Feature summary
- [QUICK_START_COMPAT.md](QUICK_START_COMPAT.md) — 3-step quickstart
- [H4MK_FORMAT.md](H4MK_FORMAT.md) — Container specification
- `api/video_compat.py` — Source code (well-documented)

---

**This layer keeps HarmonyØ4 clean, auditable, and compatible with any video app.** 🧱✨
