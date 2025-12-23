# HarmonyØ4 File Index

Complete reference of all modules, scripts, and configuration files.

## Root Configuration

- `pyproject.toml` — Python package metadata, dependencies, entry points
- `requirements.txt` — Pinned dependency versions
- `Dockerfile` — Production container image (with binary core support)
- `docker-compose.yml` — Multi-service orchestration
- `.gitignore` — Git exclusions
- `README.md` — User-facing overview
- `MANIFEST.txt` — Deployment inventory

## Documentation (docs/)

- `ARCHITECTURE.md` — System design + 4-tier separation
- `COMPRESSION_ARCHITECTURE.md` — Compression philosophy + design
- `CORE_ABI_SPEC.md` — Binary core C interface specification ✅ NEW
- `QUICK_START_API.md` — API usage examples
- `QUICK_START.md` — Getting started guide
- `DEPLOYMENT_READY.md` — Production checklist

## Core Modules

### Tier 4: Utilities (utils/)

- `crypto.py` — HKDF, SHA256, encryption utils
- `hashing.py` — Hash verification helpers

### Tier 3: Tokenizers (tokenizers/)

- `base.py` — Abstract tokenizer interface
- `video.py` — Video frame tokenization
- `video_transport.py` — Video transport encoding
- `audio_fft.py` — Audio FFT + frequency analysis

### Tier 2: Container (container/)

- `h4mk.py` — H4MK multi-track format builder (with compression) ✅ UPDATED
- `reader.py` — H4MK parser + decompression ✅ UPDATED
- `seek.py` — SEEK table operations
- `chunks.py` — Chunk protocol
- `mux/h4mk.py` — Multiplexing helpers
- `mux/h4mk_multitrack.py` — Multi-track container support

### Tier 1: API (api/)

- `main.py` — FastAPI application + routing (compress router mounted) ✅ UPDATED
- `video.py` — Video streaming endpoints
- `audio.py` — Audio streaming endpoints
- `compress.py` — Compression service endpoints ✅ NEW
- `video_range.py` — HTTP 206 range support

### Compression Subsystem (compression/)

- `api.py` — CompressionEngine abstract interface
- `geo_ref.py` — Reference compressor (RLE+delta)
- `loader.py` — Binary core loader via ctypes
- `__init__.py` — Runtime engine selector

### CLI (cli/)

- `main.py` — Command-line interface
- `compress.py` — Compression CLI tool ✅ NEW

## Scripts

### Deployment Scripts (scripts/)

- `run_dev.sh` — Development server
- `export_video.sh` — Video export utility
- `stream_audio.sh` — Audio streaming helper

## Tests

### Test Suite (tests/)

- `test_api_simple.py` — API smoke tests
- `test_audio_api.py` — Audio endpoint tests
- `test_compression.py` — Compression determinism + reversibility
- `test_crypto.py` — Cryptography unit tests
- `test_fastapi_integration.py` — Integration tests
- `test_harmony4_integration.py` — Full-stack tests
- `test_h4mk.py` — H4MK container tests
- `test_seek.py` — SEEK table tests
- `test_video_api.py` — Video endpoint tests

## Examples

### Example Code (examples/)

- `build_and_decode.py` — Container building example
- `demo_harmony4_api.py` — API usage demo

## Integration Examples

### Harmony4 Media (harmony4_media/)

- `cli.py` — Extended CLI
- `mux/gop_flags.py` — GOP flagging
- `mux/h4mk.py` — H4MK muxing
- `mux/h4mk_multitrack.py` — Multi-track support

## Adapters (adapters/)

- `base.py` — Adapter interface
- `dsp.py` — DSP adapter
- `null.py` — Null adapter

---

## Module Dependencies

```
utils/
  ↑
tokenizers/ (uses utils.crypto)
  ↑
container/ (uses tokenizers, utils)
  ↑
compression/ (independent, used by container)
  ↑
api/ (uses container, compression)
cli/ (uses compression, container)
```

---

## Key Features by File

| Feature | File(s) |
|---------|---------|
| **Compression** | compression/{api,geo_ref,loader,__init__} ✅ NEW |
| **H4MK Compression** | container/h4mk.py ✅ UPDATED |
| **H4MK Decompression** | container/reader.py ✅ UPDATED |
| **API Endpoints** | api/{main,video,audio,compress} ✅ UPDATED |
| **Binary Core Support** | compression/loader.py, Dockerfile, docker-compose.yml |
| **CLI Compression** | cli/compress.py ✅ NEW |
| **Video Streaming** | api/video.py, tokenizers/video.py |
| **Audio FFT** | tokenizers/audio_fft.py, api/audio.py |
| **Encryption** | utils/crypto.py, api/audio.py |
| **Range Requests** | api/video_range.py |
| **Deterministic Hash** | utils/crypto.py (SHA256) |

---

## Entry Points (pyproject.toml)

```toml
[project.scripts]
harmonyø4 = "cli.main:main"
harmonyø4-compress = "cli.compress:main"  ✅ NEW
```

---

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `HARMONY4_CORE_PATH` | Binary compression core location | `/opt/harmonyø4/libh4core.so` |
| `PYTHONUNBUFFERED` | Unbuffered output | `1` |
| `LOG_LEVEL` | Logging level | `info`, `debug` |

---

## Quick Navigation

**Learning Path**:
1. Start: `README.md`
2. Architecture: `docs/ARCHITECTURE.md`
3. API: `docs/QUICK_START_API.md`
4. Compression: `docs/COMPRESSION_ARCHITECTURE.md`
5. Core ABI: `docs/CORE_ABI_SPEC.md`

**Implementation Path**:
1. Tokenizers: `tokenizers/*.py`
2. Container: `container/*.py`
3. Compression: `compression/*.py`
4. API: `api/*.py`
5. Tests: `tests/*.py`

---

**Last Updated**: December 23, 2025  
**Status**: ✅ Production Ready
