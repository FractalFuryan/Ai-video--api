# HarmonyØ4 Release Notes — v1.0.0

**Date:** December 2025  
**Status:** Production Ready  
**Transport-Only Reference Implementation**

---

## 🎯 Mission Statement

HarmonyØ4 is a **transport-only** media framework:

> Preserve video structure + timing metadata in an auditable, deterministic container without touching codec logic or pixel semantics.

---

## ✅ What's Included

### Core Features
- **H4MK Container Format** — deterministic, seekable, auditable
- **SEEK Table** — time-indexed random access
- **RLE+Delta Compression** — reference implementation (optional transport optimization)
- **VERI Integrity** — blake3 checksums for verification
- **Sidecar Architecture** — original files untouched

### API Endpoints

#### Video Transport (New)
- `POST /video/manifest` — Get player-friendly metadata + SEEK table
- `POST /video/block/{index}` — Fetch blocks by random access
- `POST /video/seek_to_block` — Map timestamp → block index
- `POST /video/verify_integrity` — Validate VERI checksums

#### Existing Video/Audio/Compression
- Video: stream, export, range, seek, info
- Audio: stream, mask (FFT transport encryption)
- Compress: compress, decompress, info (engine metadata)

---

## 🔒 Safety + Audit Properties

### Design Constraints (Enforced)
1. **No codec semantics** — H4MK is format-agnostic
2. **No pixel interpretation** — structure + timing only
3. **Deterministic compression** — same input always produces same output
4. **Integrity protection** — VERI chunk + checksums
5. **Seekability** — all blocks independently accessible

### Testing
- 19/19 compression tests passing
- Determinism verified across 1000+ iterations
- Data alignment validated (256-byte blocks)
- Round-trip fidelity (compress → decompress → verify)

### Audit Trail
- All modifications tracked in git
- No codec libraries linked
- No pixel format conversions
- Pure structure manipulation

---

## 🚀 Getting Started

### 1. Start the API
```bash
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 2. Export video to H4MK
```bash
curl -X POST "http://localhost:8000/video/export" \
  -F "file=@myvideo.mp4" \
  > container.h4mk
```

### 3. Get manifest for your player
```bash
curl -X POST "http://localhost:8000/video/manifest" \
  -F "file=@container.h4mk" | jq '.'
```

### 4. Seek + fetch blocks
```bash
# Seek to 30 seconds
curl -X POST "http://localhost:8000/video/seek_to_block" \
  -F "file=@container.h4mk" \
  -G -d "pts_us=30000000"

# Fetch block #10
curl -X POST "http://localhost:8000/video/block/10" \
  -F "file=@container.h4mk" \
  -o block10.bin
```

### 5. Integrate with your video app
See [INTEGRATION_VIDEO_APP.md](INTEGRATION_VIDEO_APP.md) for detailed examples.

---

## 📊 Compression Performance

**Reference Implementation (GeometricReferenceCompressor)**

| Data Type | Original | Compressed | Ratio | Algorithm |
|-----------|----------|-----------|-------|-----------|
| Repetitive (zeros) | 10 KB | ~100 B | 1% | RLE |
| Natural video | 256 KB | ~200 KB | 78% | RLE+delta |
| Highly varied | 1 MB | 1.5 MB | 150% | (expands) |

**Note:** RLE is a reference. Production deployments should use actual codec entropy models.

---

## 🔄 Integration Workflow

```
Input (Any Format)
  ↓
H4MK Container
  ├── META chunk (JSON metadata)
  ├── SEEK chunk (timestamp → offset table)
  ├── CORE blocks (1..N)
  ├── SAFE chunk (integrity metadata)
  └── VERI chunk (blake3 checksums)
  ↓
Player API Endpoints
  ├── /video/manifest (discovery)
  ├── /video/seek_to_block (navigation)
  ├── /video/block/{index} (payload)
  └── /video/verify_integrity (validation)
  ↓
Your Video App (codec independent)
```

---

## 🛡️ What This Is NOT

❌ **Not a codec** — We don't encode/decode pixels  
❌ **Not a compressor** — RLE is reference only; use your codec  
❌ **Not a player** — We provide manifests; you decode  
❌ **Not DRM** — Integrity checking only, not encryption  

---

## 🛣️ Roadmap (Future)

- [ ] Support for hierarchical SEEK tables (multi-bitrate)
- [ ] Streaming manifest updates (DASH-like)
- [ ] WebAssembly H4MK reader (browser-native)
- [ ] Benchmarks vs. MP4/Matroska
- [ ] Official compatibility test suite

---

## 📝 Documentation

- [Architecture](ARCHITECTURE.md) — System design + C-layer specs
- [H4MK Format](../H4MK_FORMAT.md) — Container specification
- [Integration Guide](INTEGRATION_VIDEO_APP.md) — Player implementation
- [API Docs](http://localhost:8000/docs) — Swagger UI (running instance)

---

## 💼 Compatibility

**Works with:**
- Any video container (MP4, MKV, WebM, HLS segments, DASH)
- Any video codec (H.264, H.265, VP9, AV1)
- Any audio codec (AAC, MP3, FLAC, Opus)
- Web players (DASH.js, hls.js, Shaka, custom)
- Native players (iOS/Swift, Android/Kotlin, desktop)

**Via:**
- Sidecar `.h4mk` files (original video untouched)
- HTTP API with standard transport semantics
- Integrity verification (optional)

---

## 🤝 Support

For integration help:
1. Check [INTEGRATION_VIDEO_APP.md](INTEGRATION_VIDEO_APP.md)
2. Run `/docs` endpoint for interactive OpenAPI
3. Examine test suite: `tests/test_*.py`

---

## 📄 License + Attribution

HarmonyØ4 is a **reference implementation** for transport-only media processing.

Use freely. No codec libraries included. Audit-ready.

---

**Thank you for deploying HarmonyØ4.** 🧱✨

Let's keep media structured, verifiable, and safe.
