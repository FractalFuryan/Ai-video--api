# HarmonyØ4 Video Integration Guide

**Quick reference for integrating video transport into your existing app.**

---

## Installation

All code is already in the repo. No new dependencies added.

```bash
# Nothing to install! Uses existing crypto + container + compression libs.
```

---

## 1. Add API Endpoints

In `api/main.py`:

```python
from api.video_tracks import router as video_tracks_router
app.include_router(video_tracks_router)

# Now you have:
# POST /video/manifest
# POST /video/seek_to_block
# POST /video/block
```

---

## 2. Create H4MK Sidecars

```python
from video.track import TrackBlock
from video.gop import GOPConfig, kind_for
from container.h4mk_tracks import build_h4mk_tracks

# Your frames
frames = [...]  # list of frame bytes

# Create blocks
cfg = GOPConfig(gop_size=30)
blocks = [
    TrackBlock(
        track_id="video_main",
        pts_us=i * 33333,  # 30fps
        kind=kind_for(i, cfg),
        keyframe=(i % 30) == 0,
        payload=frame_bytes,
    )
    for i, frame_bytes in enumerate(frames)
]

# Pack
h4mk_sidecar = build_h4mk_tracks(
    blocks,
    meta={"title": "my_video", "fps": 30},
    safe={"policy": "transport_only"},
)

# Save
open("video.h4mk", "wb").write(h4mk_sidecar)
```

---

## 3. Seek on Client

```python
# POST /video/manifest
response = requests.post(
    "http://server/video/manifest",
    files={"file": open("video.h4mk", "rb")},
)
manifest = response.json()
print(manifest["tracks"])  # ["video_main", "controls", ...]
print(manifest["seek"])    # per-track keyframes

# POST /video/seek_to_block
response = requests.post(
    "http://server/video/seek_to_block",
    files={"file": open("video.h4mk", "rb")},
    params={"track_id": "video_main", "pts_us": 5000000},
)
seek_result = response.json()
core_index = seek_result["core_index"]

# POST /video/block
response = requests.post(
    "http://server/video/block",
    files={"file": open("video.h4mk", "rb")},
    params={"core_index": core_index, "decompress": True},
)
block_bytes = response.content
```

---

## 4. CLI Usage

```bash
# Inspect container
harmonyØ4-video manifest video.h4mk

# Find keyframe
harmonyØ4-video seek video.h4mk --track video_main --pts_us 5000000

# Fetch block
harmonyØ4-video block video.h4mk --index 42 --output frame.bin
```

---

## 5. Optional: Encrypt with LivingCipher

```python
from crypto.living_cipher import init_from_shared_secret
from crypto.living_bindings import CoreContext, encrypt_core_block

# Setup cipher
shared_secret = b"..."  # from X25519 handshake
state = init_from_shared_secret(shared_secret)

# For each block
ctx = CoreContext(
    engine_id="geom-ref",
    engine_fp="...",
    container_veri_hex="...",  # VERI hash from H4MK
    track_id="video_main",
    pts_us=5000,
    chunk_index=i,
)
header, ciphertext = encrypt_core_block(state, block_payload, ctx)
```

---

## Properties

- ✅ **Transport-only** (no pixels, no identity)
- ✅ **Readable metadata** (no decryption needed to seek)
- ✅ **Fast seeking** (O(log n) on keyframes)
- ✅ **Optional encryption** (LivingCipher with context binding)
- ✅ **Auditable** (all metadata inspectable)
- ✅ **Zero breaking changes** (sidecar model)

---

## Files

| File | Purpose |
|------|---------|
| `video/adapter.py` | Codec contract (ABC) |
| `video/controls.py` | Camera/motion (no identity) |
| `video/gop.py` | Keyframe scheduling |
| `video/track.py` | Track + block metadata |
| `container/multitrack.py` | TRAK + SEEKM packing |
| `container/h4mk_tracks.py` | H4MK builder |
| `crypto/living_bindings.py` | Cipher context binding |
| `api/video_tracks.py` | FastAPI endpoints |
| `cli/video_tools.py` | CLI tools |
| `tests/test_video_transport.py` | Tests |

---

## Troubleshooting

**Q: How do I handle variable frame rates?**  
A: Just set `pts_us` to the actual presentation timestamp. Seeking works on any timeline.

**Q: Can I add custom metadata per block?**  
A: Yes! Extend `TrackBlock` or store in META. TRAK is read-only for transport safety.

**Q: What if I want B-frames?**  
A: Set `GOPConfig(allow_b=True)`. The codec adapter handles apply_B.

**Q: Is seeking encrypted?**  
A: No, TRAK and SEEKM are readable. Only CORE blocks are encrypted (optional).

---

**That's it! 🚀 Video transport is now part of HarmonyØ4.**
