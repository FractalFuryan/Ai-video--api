# HarmonyØ4 Video Compatibility — Quick Start

**Status:** ✅ Production Ready  
**Integration Model:** Sidecar + REST API  
**Safety Level:** Transport-only (no codec/pixel logic)

---

## 3-Step Integration

### 1️⃣ Export Your Video to H4MK

```bash
curl -X POST http://localhost:8000/video/export \
  -F "file=@myvideo.mp4" \
  --output container.h4mk
```

### 2️⃣ Get Manifest for Your Player

```bash
curl -X POST http://localhost:8000/video/manifest \
  -F "file=@container.h4mk" | jq .
```

Returns: `blocks`, `seek` table, `compression`, metadata

### 3️⃣ On User Seek → Fetch Block

```bash
# User seeks to 30 seconds (30,000,000 microseconds)
curl -X POST http://localhost:8000/video/seek_to_block \
  -F "file=@container.h4mk" \
  -G -d "pts_us=30000000"

# Response: { "keyframe_entry_index": 15, ... }

# Fetch that block
curl -X POST http://localhost:8000/video/block/15 \
  -F "file=@container.h4mk" \
  --output block15.bin

# Decode with your codec (MP4, H.264, VP9, etc. — unchanged)
```

---

## API Reference

| Endpoint | Method | Purpose | Input | Output |
|----------|--------|---------|-------|--------|
| `/video/manifest` | POST | Get SEEK table + metadata | .h4mk file | JSON manifest |
| `/video/seek_to_block` | POST | Map timestamp → block index | .h4mk + pts_us | Block index |
| `/video/block/{index}` | POST | Fetch block by index | .h4mk + index | Binary payload |
| `/video/verify_integrity` | POST | Check VERI checksums | .h4mk file | Integrity report |

---

## Code Examples

### JavaScript (Web Player)

```javascript
async function playH4MK(h4mkFile) {
  // Get manifest
  const fd = new FormData();
  fd.append('file', h4mkFile);
  const manifest = await fetch('/video/manifest', {
    method: 'POST',
    body: fd
  }).then(r => r.json());

  // User seeks to 30s
  const seekFd = new FormData();
  seekFd.append('file', h4mkFile);
  const seek = await fetch('/video/seek_to_block?pts_us=30000000', {
    method: 'POST',
    body: seekFd
  }).then(r => r.json());

  // Fetch block
  const blockFd = new FormData();
  blockFd.append('file', h4mkFile);
  const block = await fetch(
    `/video/block/${seek.keyframe_entry_index}`,
    { method: 'POST', body: blockFd }
  ).then(r => r.arrayBuffer());

  // Decode (your codec library)
  player.appendBuffer(block);
}
```

### Python (Backend)

```python
import requests

def get_block_for_time(h4mk_path: str, seek_seconds: float):
    # Seek
    with open(h4mk_path, 'rb') as f:
        resp = requests.post(
            'http://localhost:8000/video/seek_to_block',
            files={'file': f},
            params={'pts_us': int(seek_seconds * 1_000_000)}
        )
    block_idx = resp.json()['keyframe_entry_index']

    # Fetch
    with open(h4mk_path, 'rb') as f:
        resp = requests.post(
            f'http://localhost:8000/video/block/{block_idx}',
            files={'file': f},
            params={'decompress': True}
        )
    return resp.content  # Binary payload
```

### cURL (One-liner Testing)

```bash
# Full workflow
H4MK=container.h4mk

# 1. Get manifest
curl -s -X POST http://localhost:8000/video/manifest \
  -F "file=@$H4MK" | jq '.seek | length'

# 2. Seek to 1 minute
BLOCK=$(curl -s -X POST http://localhost:8000/video/seek_to_block \
  -F "file=@$H4MK" \
  -G -d "pts_us=60000000" | jq '.keyframe_entry_index')

# 3. Fetch block
curl -X POST http://localhost:8000/video/block/$BLOCK \
  -F "file=@$H4MK" \
  -o block.bin && ls -lh block.bin
```

---

## Integration Checklist

- [ ] Deploy HarmonyØ4 API (`api/main.py`)
- [ ] Export video: `POST /video/export`
- [ ] Get manifest: `POST /video/manifest`
- [ ] Implement seek handler: call `POST /video/seek_to_block`
- [ ] Implement block fetcher: call `POST /video/block/{index}`
- [ ] Pass blocks to your codec (unchanged)
- [ ] (Optional) Add integrity check: `POST /video/verify_integrity`
- [ ] Cache blocks locally for smooth playback
- [ ] Test seeking across different timestamps

---

## Safety Guarantees

✅ **What HarmonyØ4 does:**
- Structure preservation (SEEK table)
- Integrity verification (VERI checksums)
- Deterministic compression (RLE reference)
- Transport optimization (block-based)

❌ **What HarmonyØ4 does NOT do:**
- Codec logic
- Pixel manipulation
- Audio waveform processing
- DRM or encryption

**Result:** Safe for **any video format** (MP4, MKV, HLS, DASH, etc.)

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `422 Invalid H4MK container` | Ensure file was exported via `/video/export` |
| `416 Block index out of range` | Check manifest `blocks` count; index too high |
| `500 Seek mapping failed` | Container may be corrupted; run `/video/verify_integrity` |
| `file: command not found` | Use `curl -F "file=@..."` or pass FormData in code |

---

## Full Documentation

See [INTEGRATION_VIDEO_APP.md](docs/INTEGRATION_VIDEO_APP.md) for:
- Detailed API specs
- Web / Native / Python examples
- HLS / DASH / MP4 adaptation
- Caching strategies

---

**Ready to integrate?** Start with **Step 1** above. 🚀
