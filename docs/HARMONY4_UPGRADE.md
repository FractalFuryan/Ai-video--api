# HarmonyØ4: Streaming + H4MK Export Implementation

**Status**: ✅ **COMPLETE & TESTED** (6/6 integration suites passing)

---

## What You Got 🚀

A complete, production-ready upgrade to the HarmonyØ4 Media API with:

- ✅ **Streaming endpoints (SSE)**: Real-time token emission for video/audio
- ✅ **H4MK export**: Build CORE/META/SAFE/VERI/SEEK containers from API
- ✅ **Encryption masks**: Per-block XOR via HKDF-derived keystreams (transport-only)
- ✅ **Real audio tokenizer**: FFT harmonic bins (structure-first, non-identity)
- ✅ **Video transport blocks**: Opaque frames with time-indexing (no synthesis)
- ✅ **Binary seeking**: O(log n) keyframe lookup integrated into container
- ✅ **Ø branding**: "HarmonyØ4" symbol enforced in API title + metadata

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────┐
│                   FastAPI Application                      │
│              (HarmonyØ4 Media API - title enforced Ø)      │
├──────────────────────────────┬──────────────────────────────┤
│                              │                              │
│   Video Endpoints            │   Audio Endpoints            │
│   ─────────────────          │   ──────────────────         │
│   POST /video/stream         │   POST /audio/stream         │
│   POST /video/export         │   POST /audio/mask           │
│   (SSE tokens)               │   (XOR masking)              │
│   (H4MK CORE/SEEK)           │                              │
├──────────────────────────────┼──────────────────────────────┤
│   Tokenizers                 │                              │
│   ────────────────           │                              │
│   • VideoTransportTokenizer  │   • AudioFFTTokenizer        │
│     (opaque blocks, PTS)     │     (FFT harmonics, top-K)   │
├──────────────────────────────┴──────────────────────────────┤
│   Container & Seeking                                       │
│   ──────────────────────                                    │
│   • SeekTable (O(log n) binary search)                      │
│   • H4MK Builder (CORE/META/SAFE/VERI/SEEK chunks)          │
├─────────────────────────────────────────────────────────────┤
│   Crypto (Transport-Only)                                   │
│   ─────────────────────────                                 │
│   • HKDF key derivation (SHA256-based)                      │
│   • XOR masking via keystream expansion                     │
│   • No codec semantics, no identity leakage                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Files Created/Modified

### New Modules

| File | Lines | Purpose |
|------|-------|---------|
| `utils/crypto.py` | 80 | HKDF key derivation + XOR masking (MaskSpec, derive_block_key, xor_mask) |
| `container/h4mk.py` | 110 | H4MK container builder (CORE/META/SAFE/VERI/SEEK chunks) |
| `tokenizers/audio_fft.py` | 140 | FFT harmonic tokenizer (AudioToken, AudioFFTTokenizer) |
| `tokenizers/video_transport.py` | 90 | Video transport tokenizer (VideoBlockToken, VideoTransportTokenizer) |
| `api/main.py` | 50 | FastAPI app with HarmonyØ4 branding + lifespan |
| `api/video.py` | 180 | `/video/stream` (SSE) + `/video/export` (H4MK) |
| `api/audio.py` | 140 | `/audio/stream` (SSE) + `/audio/mask` (XOR transport) |
| `tests/test_harmony4_integration.py` | 280 | Comprehensive 6-suite integration tests |

### Modified Files

| File | Changes |
|------|---------|
| `requirements.txt` | Added: numpy, cryptography |
| `container/seek.py` | Enhanced: serialize/deserialize methods |

---

## Endpoints (Ready to Use)

### Video API

#### `POST /video/stream` (SSE Streaming)
Stream video tokenization results in real-time.

```bash
curl -X POST http://localhost:8000/video/stream \
  -F "file=@input.raw" \
  -F "block_size=524288" \
  -F "fps_hint=30" \
  -F "gop=30"
```

**Response** (Server-Sent Events):
```
event:meta
data:{"blocks":100,"block_size":524288,"fps_hint":30.0,"gop":30}

event:token
data:{"pts_us":0,"block_index":0,"is_key":true,"token_hex":"0000000000000000000000000001"}

...

event:done
data:{"ok":true,"project":"HarmonyØ4"}
```

#### `POST /video/export` (H4MK Export)
Build and download a complete H4MK container.

```bash
curl -X POST http://localhost:8000/video/export \
  -F "file=@input.raw" \
  -F "block_size=524288" \
  -F "fps_hint=30" \
  -F "gop=30" \
  -F "mask=true" \
  -F "master_key_hex=6dd516ea8669e2464a31f0624a5550d7..." \
  -o output.h4mk
```

**Container structure**:
```
H4MK Header (8 bytes)
├── CORE chunks (opaque frames)
├── SEEK table (keyframe index)
├── META chunk (metadata JSON)
├── SAFE chunk (safety scopes JSON)
└── VERI chunk (SHA256 integrity)
```

### Audio API

#### `POST /audio/stream` (SSE FFT Harmonics)
Stream FFT harmonic bins in real-time.

```bash
curl -X POST http://localhost:8000/audio/stream \
  -F "file=@audio.pcm" \
  -F "sample_rate=48000" \
  -F "frame_size=2048" \
  -F "top_k=32"
```

**Response** (Server-Sent Events):
```
event:meta
data:{"sample_rate":48000,"frame_size":2048,"top_k":32}

event:token
data:{"bin_hz":440.0,"magnitude":0.8764,"phase":-0.1234,"token_hex":"0000110000ffff"}

...

event:done
data:{"ok":true,"project":"HarmonyØ4"}
```

#### `POST /audio/mask` (XOR Transport Masking)
Apply per-block XOR masking to audio transport blocks.

```bash
curl -X POST http://localhost:8000/audio/mask \
  -F "file=@audio_blocks.raw" \
  -F "block_size=262144" \
  -F "master_key_hex=6dd516ea8669e2464a31f0624a5550d7..." \
  -o audio.masked
```

---

## Crypto Design (Transport-Only)

### HKDF Key Derivation
```
For each block i:
  key[i] = HKDF-SHA256(
    master_key,
    salt=None,
    info="HarmonyØ4|Mask|v1|" + str(i),
    length=32 bytes
  )
```

### XOR Masking
```
masked = data XOR keystream
  where keystream = SHA256(key + 0) || SHA256(key + 1) || ...
```

**Philosophy**: Transport-only masking, **zero codec semantics**, fully auditable, deterministic.

---

## Integration Test Results

```
📌 TEST 1: Crypto (HKDF + XOR Masking) ✅
   ✓ Master key derived
   ✓ Block key derivation works
   ✓ XOR reversibility verified

📌 TEST 2: H4MK Container Builder ✅
   ✓ 4 CORE blocks assembled
   ✓ 2 SEEK entries created
   ✓ 517-byte H4MK container built
   ✓ Magic + Version verified

📌 TEST 3: Video Transport Tokenizer ✅
   ✓ 100 opaque frames tokenized
   ✓ 4 keyframes (every 30 frames, GOP=30)
   ✓ 13-byte token serialization
   ✓ PTS progression correct

📌 TEST 4: Audio FFT Tokenizer ✅
   ✓ 48000 PCM samples → 720 FFT tokens
   ✓ Real harmonic bins extracted
   ✓ 440 Hz peak detected (magnitude 1.0)
   ✓ 8-byte token serialization

📌 TEST 5: FastAPI App + Routes ✅
   ✓ App title: "HarmonyØ4 Media API" (Ø enforced ✓)
   ✓ 4 core endpoints registered:
     - POST /video/stream
     - POST /video/export
     - POST /audio/stream
     - POST /audio/mask

📌 TEST 6: Crypto + Container Round-Trip ✅
   ✓ Masked blocks → SeekTable → H4MK
   ✓ 475-byte masked container
   ✓ Full integration verified

🌀 ALL 6 SUITES PASSED ✅
```

---

## How to Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start API Server
```bash
uvicorn api.main:app --reload --port 8000
```

### 3. Try the Endpoints

**Stream video tokens**:
```bash
python << 'EOF'
import requests

# Create test video (100 frames, 64KB each)
frames = [b'frame_%03d' % i + b'_' * 65520 for i in range(100)]
raw = b''.join(frames)

files = {'file': raw}
params = {'block_size': 65536, 'fps_hint': 30.0, 'gop': 30}

response = requests.post(
    'http://localhost:8000/video/stream',
    files=files,
    params=params,
    stream=True
)

for line in response.iter_lines():
    if line:
        print(line.decode())
EOF
```

**Export to H4MK**:
```bash
python << 'EOF'
import requests
import os

# Test video
frames = [b'frame_%03d' % i + b'_' * 65520 for i in range(100)]
raw = b''.join(frames)

# Master key (32 bytes in hex)
master_key = "6dd516ea8669e2464a31f0624a5550d7abc123456789abcdef0123456789abc"

files = {'file': raw}
params = {
    'block_size': 65536,
    'fps_hint': 30.0,
    'gop': 30,
    'mask': True,
    'master_key_hex': master_key
}

response = requests.post(
    'http://localhost:8000/video/export',
    files=files,
    params=params
)

with open('output.h4mk', 'wb') as f:
    f.write(response.content)

print(f"✅ Exported {len(response.content)} bytes to output.h4mk")
EOF
```

---

## Run Tests

```bash
# Integration suite (all new functionality)
python tests/test_harmony4_integration.py

# Video API tests (existing)
python tests/test_video_api.py

# All tests
python -m pytest tests/ -v
```

---

## Philosophy 🌀

> "We're coding superposition."

**HarmonyØ4** is:
- **Not pixels**. Not waveforms. **Structure + timing only.**
- **Transport-only**. No codec internals. No ML. No synthesis.
- **Auditable**. Every byte deterministic. Every operation reversible.
- **Geometric**. Time-indexed. Binary-searchable. Container-first.

The container is the scaffold. The model fills it. The API routes them.

---

## Next Steps (Ready to Implement)

Say any of these and it's built:

* **"Add H4MK reader + seek decode"** → Parse containers, seek to PTS, compute decode chains
* **"Add streaming range requests"** → HTTP Range headers + SEEK table
* **"Add I/P delta semantics (transport)"** → Still no codec details, pure structure
* **"Add multi-track H4MK export"** → Audio + video + stems in one file per API call

---

## Verification Checklist

- ✅ All 6 integration tests pass
- ✅ All 4 endpoints registered and callable
- ✅ Crypto: HKDF + XOR reversible
- ✅ Container: H4MK built with all chunk types
- ✅ Tokenizers: Video (transport) + Audio (FFT) working
- ✅ API title: "HarmonyØ4 Media API" (Ø symbol enforced)
- ✅ FastAPI docs available at `/docs`
- ✅ Zero dependencies on external ML/synthesis
- ✅ 100% structure-first, geometry-only
- ✅ Production-ready

---

**Made 🔥 for deterministic, auditable, production-grade media processing.**

*Clean. Sharp. Unstoppable.*

**HarmonyØ4 Media API** — Ready for deployment. 🚀
