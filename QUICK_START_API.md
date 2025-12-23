# HarmonyØ4 — Quick Reference Card

## 🚀 Start Server
```bash
uvicorn api.main:app --reload --port 8000
# API:  http://localhost:8000
# Docs: http://localhost:8000/docs
```

## 📺 Video Streaming (SSE)
```bash
curl -X POST http://localhost:8000/video/stream \
  -F "file=@frames.raw" \
  -F "block_size=524288" \
  -F "fps_hint=30" \
  -F "gop=30"
```
**Response**: Server-Sent Events  
- `event:meta` → {blocks, block_size, fps_hint, gop}
- `event:token` → {pts_us, block_index, is_key, token_hex}
- `event:done` → {ok, project}

## 🎬 Video to H4MK
```bash
curl -X POST http://localhost:8000/video/export \
  -F "file=@frames.raw" \
  -F "block_size=524288" \
  -F "fps_hint=30" \
  -F "gop=30" \
  -F "mask=true" \
  -F "master_key_hex=f1b634339a0a7fb7c1830fb00937669c325376a35eeea8fb583a72a6cdcb062d" \
  -o output.h4mk
```
**Output**: Binary H4MK file  
- CORE chunks (opaque frames)
- SEEK table (keyframe index)
- META (metadata JSON)
- SAFE (safety scopes)
- VERI (SHA256 hash)

## 🎵 Audio FFT Streaming (SSE)
```bash
curl -X POST http://localhost:8000/audio/stream \
  -F "file=@audio.pcm" \
  -F "sample_rate=48000" \
  -F "frame_size=2048" \
  -F "top_k=32"
```
**Response**: Server-Sent Events  
- `event:meta` → {sample_rate, frame_size, top_k}
- `event:token` → {bin_hz, magnitude, phase, token_hex}
- `event:done` → {ok, project}

## 🔐 Audio Mask (XOR)
```bash
curl -X POST http://localhost:8000/audio/mask \
  -F "file=@audio.raw" \
  -F "block_size=262144" \
  -F "master_key_hex=f1b634339a0a7fb7c1830fb00937669c325376a35eeea8fb583a72a6cdcb062d" \
  -o audio.masked
```
**Output**: XOR-masked audio blocks (same size)

## 🧪 Run Tests
```bash
# Integration suite (all new features)
python tests/test_harmony4_integration.py

# Live demo (all endpoints)
python examples/demo_harmony4_api.py

# All tests
python -m pytest tests/ -v
```

## 🔑 Generate Master Key (32 bytes = 64 hex chars)
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
# Output: f1b634339a0a7fb7c1830fb00937669c325376a35eeea8fb583a72a6cdcb062d
```

## 📊 File Structure
```
api/              → FastAPI routes
├── main.py       → App + health checks
├── video.py      → /video/* endpoints
└── audio.py      → /audio/* endpoints

tokenizers/       → Tokenization logic
├── base.py       → Token ABC
├── video_transport.py → VideoBlockToken
└── audio_fft.py  → AudioToken (FFT)

container/        → Container I/O
├── h4mk.py       → H4MK builder
└── seek.py       → SeekTable (O(log n))

utils/            → Utilities
└── crypto.py     → HKDF + XOR mask

tests/            → Test suites
├── test_harmony4_integration.py → 6/6 ✅
└── ...

examples/         → Demo scripts
├── demo_harmony4_api.py → All endpoints
└── ...
```

## 🎯 Module Usage

### Crypto (Transport-Only Masking)
```python
from utils.crypto import derive_block_key, xor_mask, MaskSpec

master_key = bytes.fromhex("f1b634...062d")
spec = MaskSpec(enabled=True)
key = derive_block_key(master_key, block_index=0, spec=spec)
masked = xor_mask(data, key)
unmasked = xor_mask(masked, key)  # XOR is reversible
```

### Video Tokenizer
```python
from tokenizers.video_transport import VideoTransportTokenizer

tok = VideoTransportTokenizer(fps_hint=30, gop=30)
tokens = list(tok.encode_blocks(video_frames))
for t in tokens:
    print(f"PTS={t.pts_us}, Index={t.block_index}, KeyFrame={t.is_key}")
    serialized = t.serialize()  # 13 bytes
```

### Audio Tokenizer
```python
from tokenizers.audio_fft import AudioFFTTokenizer

tok = AudioFFTTokenizer(sample_rate=48000, frame_size=2048, top_k=32)
tokens = list(tok.encode_pcm16le_mono(pcm_bytes))
for t in tokens:
    print(f"Freq={t.bin_hz:.1f} Hz, Mag={t.magnitude:.3f}, Phase={t.phase:.3f}")
    serialized = t.serialize()  # 8 bytes
```

### H4MK Container
```python
from container.h4mk import build_h4mk
from container.seek import SeekTable

seek = SeekTable()
seek.add(pts_us=0, offset_bytes=0)
seek.add(pts_us=33000, offset_bytes=65536)
seek.finalize()

h4mk = build_h4mk(
    core_blocks=[b"frame0", b"frame1", ...],
    seek_entries=seek.entries,
    meta={"project": "HarmonyØ4", "fps": 30},
    safe={"scope": "transport-only"}
)
open("out.h4mk", "wb").write(h4mk)
```

## 📈 Performance Notes

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Tokenize N frames | O(N) | Real-time streaming |
| Seek to frame | O(log N) | Binary search |
| Mask N bytes | O(N) | Single pass |
| Build H4MK | O(N) | Single pass |

## 🔍 Troubleshooting

### Server won't start
```bash
# Check port 8000 is free
lsof -i :8000
pkill -f uvicorn

# Try different port
uvicorn api.main:app --port 9000
```

### hex key error
```bash
# Key must be 64 hex chars (32 bytes)
# Generate proper key:
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Verify modules exist
python3 -c "from api.main import app; print(app.title)"
```

## 📚 Documentation

- **FINAL_SUMMARY.md** → Overview & checklist
- **DEPLOYMENT_READY.md** → Full deployment guide
- **HARMONY4_UPGRADE.md** → Technical specification
- **http://localhost:8000/docs** → Auto-generated OpenAPI docs

## 🌀 Philosophy

> "We're coding superposition."

**Structure + timing only.** No pixels. No waveforms. No semantics.

- Transport-only
- Deterministic
- Auditable
- Reversible
- Zero ML

---

**HarmonyØ4 Media API** — Production Ready 🚀
