# HarmonyØ4 Video Transport Port Packet

**Status:** Complete transport-only sidecar for existing video apps.  
**Safety:** No pixels, no synthesis, no identity. Pure data flow + seeking.

---

## What You Get

### 1. **Multitrack Support**
- Multiple video/audio/control tracks in one container
- Each track has its own timeline + keyframes
- Readable track index (no decryption needed)

### 2. **Fast Seeking**
- Per-track seek tables (readable, ~10 bytes per keyframe)
- O(log n) lookup via binary search
- Works on remote streams (streaming-friendly)

### 3. **Readable Metadata**
- Track index (`TRAK`): pts, kind, keyframe flag, core_index
- Seek tables (`SEEKM`): tracks + keyframe positions
- No decryption required to find anything

### 4. **Block-Level Encryption (Optional)**
- Use `LivingCipher` to encrypt CORE blocks
- Context binding prevents transplant across containers
- Transcript binding for tamper-evidence

### 5. **API Endpoints**
```
POST /video/manifest           -> track list + seek tables
POST /video/seek_to_block      -> find keyframe for pts
POST /video/block?index=...    -> fetch raw or decompressed
```

### 6. **CLI Tools**
```bash
harmonyØ4-video manifest file.h4mk
harmonyØ4-video seek file.h4mk --track video_main --pts_us 5000
harmonyØ4-video block file.h4mk --index 10
```

---

## Architecture

### Layers

```
┌─────────────────────────────────────┐
│  Existing Video App (MP4, HLS, etc) │
│  (Keeps its own format)             │
└─────────────────────────────────────┘
            ↓ (sidecar)
┌─────────────────────────────────────┐
│  HarmonyØ4 H4MK Video Sidecar       │
│  - Multitrack blocks (CORE)         │
│  - Track index (TRAK)               │
│  - Seek tables (SEEKM)              │
│  - Optional cipher (LivingCipher)   │
└─────────────────────────────────────┘
```

### Container Layout

```
H4MK [
  META {
    "domain": "video-transport",
    "tracks": ["video_main", "controls"],
    "seekm_b64": "...",           # base64-encoded SEEKM
    "trak_b64": "...",            # base64-encoded TRAK
    ...
  },
  SAFE { "policy": "transport_only" },
  CORE [
    block_0, block_1, block_2, ... (opaque payloads)
  ],
  VERI { hash_chain },
]
```

---

## Usage Examples

### Python API

```python
from video.track import TrackBlock
from container.h4mk_tracks import build_h4mk_tracks

# Create blocks
blocks = [
    TrackBlock("video_main", pts_us=0, kind="I", keyframe=True, payload=b"..."),
    TrackBlock("video_main", pts_us=1000, kind="P", keyframe=False, payload=b"..."),
]

# Pack into H4MK
h4mk_bytes = build_h4mk_tracks(blocks, meta={}, safe={})

# Read and seek
from container.reader import H4MKReader
r = H4MKReader(h4mk_bytes)
core_blocks = r.get_chunks(b"CORE")
```

### FastAPI

```python
from api.video_tracks import router as video_router
app.include_router(video_router)

# POST /video/manifest
# POST /video/seek_to_block?track_id=video_main&pts_us=5000
# POST /video/block?core_index=10&decompress=true
```

### CLI

```bash
harmonyØ4-video manifest file.h4mk
# {
#   "tracks": ["video_main", "controls"],
#   "seek_tracks": ["video_main", "controls"],
#   "core_blocks": 42
# }

harmonyØ4-video seek file.h4mk --track video_main --pts_us 5000
# track=video_main pts_us=5000 -> keyframe_pts_us=4000 core_index=20

harmonyØ4-video block file.h4mk --index 20
# wrote block.bin (decompressed, 65536 bytes)
```

---

## Encryption (Optional)

Use `LivingCipher` to encrypt blocks with context binding:

```python
from crypto.living_cipher import init_from_shared_secret, encrypt, decrypt
from crypto.living_bindings import CoreContext, encrypt_core_block

state = init_from_shared_secret(shared_secret)

ctx = CoreContext(
    engine_id="geom-ref",
    engine_fp="...",
    container_veri_hex="deadbeef...",
    track_id="video_main",
    pts_us=5000,
    chunk_index=10,
)

header, ciphertext = encrypt_core_block(state, payload, ctx)
decrypted = decrypt_core_block(state, header, ciphertext, ctx)
```

---

## Properties

✅ **Transport-only:** No pixel semantics, no synthesis, no identity inference  
✅ **Readable metadata:** Seek tables + track index don't require decryption  
✅ **Fast seeking:** O(log n) on keyframe tables  
✅ **Auditable:** All metadata and structure inspectable  
✅ **Tamper-evident:** Optional cipher with context binding + transcript  
✅ **Backward-compatible:** Existing video apps unchanged (sidecar model)

---

## Files

- `video/adapter.py` — Codec adapter ABC
- `video/controls.py` — Non-identity camera/motion controls
- `video/gop.py` — Keyframe scheduling
- `video/track.py` — Track + block metadata
- `container/multitrack.py` — TRAK + SEEKM packing
- `container/h4mk_tracks.py` — H4MK builder
- `crypto/living_bindings.py` — Cipher context binding
- `api/video_tracks.py` — FastAPI endpoints
- `cli/video_tools.py` — CLI tools
- `tests/test_video_transport.py` — Test suite

---

## Next Steps

1. **Integrate with your app:** Mount `/api/video_tracks.py` endpoints in FastAPI
2. **Pack video:** Use `build_h4mk_tracks()` to create H4MK sidecars
3. **Seek on client:** Use `/video/seek_to_block` to find keyframes
4. **Encrypt (optional):** Bind LivingCipher for full confidentiality + tamper-evidence

**Zero breaking changes. Zero new external deps. Pure transport. 🚀**
