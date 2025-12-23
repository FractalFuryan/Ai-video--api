# HarmonyØ4 Video App Integration Guide

## Overview

HarmonyØ4 integrates with existing video apps via a **sidecar manifest + random-access block fetch** approach. This keeps your video player untouched while providing transport-level benefits:

- **No codec assumptions** — works with any video format
- **No pixel semantics** — structure + timing only
- **Safe streaming** — integrity verification included
- **Random access** — efficient seeking and scrubbing

---

## Integration Flow

```
Your Video App
     ↓
  Upload .h4mk container to HarmonyØ4
     ↓
  GET /video/manifest (get SEEK table + metadata)
     ↓
  User seeks to time T
     ↓
  POST /video/seek_to_block?pts_us=T (find nearest keyframe)
     ↓
  GET /video/block/{index} (fetch payload)
     ↓
  Pass to your video decoder (MP4, H.264, etc. — unchanged)
```

---

## Endpoints

### 1. **Get Manifest** (initialization)

```bash
curl -X POST "http://localhost:8000/video/manifest" \
  -F "file=@container.h4mk"
```

**Response:**
```json
{
  "container": "H4MK",
  "project": "HarmonyØ4",
  "domain": "video-transport",
  "blocks": 42,
  "seek": [
    {"pts_us": 0, "block_offset": 512},
    {"pts_us": 33333, "block_offset": 4096},
    {"pts_us": 66666, "block_offset": 8192}
  ],
  "compression": {"algorithm": "RLE+delta", "ratio": 0.75},
  "safe": {"version": "1.0"}
}
```

**Use this to:**
- Initialize your player UI with total duration
- Build scrubber timeline from seek table
- Display compression stats

---

### 2. **Seek to Timestamp** (on user scrub)

```bash
curl -X POST "http://localhost:8000/video/seek_to_block" \
  -F "file=@container.h4mk" \
  -G -d "pts_us=100000000"  # 100 seconds in microseconds
```

**Response:**
```json
{
  "pts_us": 100000000,
  "keyframe_entry_index": 15,
  "keyframe_pts_us": 99999000
}
```

**Use this to:**
- Map scrubber position → block index
- Find nearest keyframe for that timestamp
- Pass `keyframe_entry_index` to `/video/block/{index}`

---

### 3. **Fetch Block** (random access)

```bash
curl -X POST "http://localhost:8000/video/block/15" \
  -F "file=@container.h4mk" \
  -G -d "decompress=true"
```

**Response:** Binary payload (application/octet-stream)

**Use this to:**
- Feed decompressed block to your video decoder
- Cache blocks locally for smooth playback
- Implement adaptive bitrate by requesting lower-quality blocks

---

### 4. **Verify Integrity** (optional, for production)

```bash
curl -X POST "http://localhost:8000/video/verify_integrity" \
  -F "file=@container.h4mk"
```

**Response:**
```json
{
  "valid": true,
  "hash_algorithm": "blake3",
  "info": "VERI check passed; 42 block(s) verified"
}
```

**Use this to:**
- Verify file hasn't been corrupted before playback
- Detect tampered containers (if VERI chunk present)

---

## Implementation Examples

### Web Player (JavaScript + Fetch)

```javascript
async function playH4MK(containerFile) {
  // 1. Get manifest
  const manifest = await fetch('/video/manifest', {
    method: 'POST',
    body: new FormData({ file: containerFile })
  }).then(r => r.json());

  // 2. Initialize player UI
  const duration = manifest.seek[manifest.seek.length - 1].pts_us / 1e6;
  player.setDuration(duration);

  // 3. On seek
  player.addEventListener('seeking', async (event) => {
    const seekResult = await fetch('/video/seek_to_block', {
      method: 'POST',
      body: new FormData({ file: containerFile }),
      headers: { 'X-PTS-US': Math.floor(event.target.currentTime * 1e6) }
    }).then(r => r.json());

    const blockIndex = seekResult.keyframe_entry_index;

    // 4. Fetch block
    const blockData = await fetch(`/video/block/${blockIndex}`, {
      method: 'POST',
      body: new FormData({ file: containerFile })
    }).then(r => r.arrayBuffer());

    // 5. Decode with your codec (H.264, VP9, etc.)
    player.appendBuffer(blockData);
  });
}
```

### Python Client

```python
import requests
import json

def integrate_h4mk(container_path: str):
    with open(container_path, 'rb') as f:
        # Get manifest
        resp = requests.post(
            'http://localhost:8000/video/manifest',
            files={'file': f}
        )
        manifest = resp.json()
        print(f"Duration: {manifest['seek'][-1]['pts_us'] / 1e6}s")
        print(f"Blocks: {manifest['blocks']}")

    # Seek to 30 seconds
    with open(container_path, 'rb') as f:
        resp = requests.post(
            'http://localhost:8000/video/seek_to_block',
            files={'file': f},
            params={'pts_us': 30_000_000}
        )
        seek_result = resp.json()
        block_idx = seek_result['keyframe_entry_index']

    # Fetch block
    with open(container_path, 'rb') as f:
        resp = requests.post(
            f'http://localhost:8000/video/block/{block_idx}',
            files={'file': f},
            params={'decompress': True}
        )
        block_payload = resp.content
        # Pass to your decoder...
```

---

## Safety Notes

✅ **Safe by design:**
- No codec dependencies
- No pixel data interpretation
- VERI integrity checks available
- Original video file untouched (sidecar only)

⚠️ **Before production:**
1. Call `/video/verify_integrity` on container before playback
2. Validate manifest schema matches your expectations
3. Handle seek/block errors gracefully (HTTP 416, 422, 500)
4. Cache blocks locally to avoid re-fetching

---

## For Your Video App Specifics

**If you're using:**
- **HLS:** Adapt seek table to segment boundaries
- **DASH:** Use manifest to generate adaptive bitrate ladder
- **MP4 + DASH.js:** Map blocks to MP4 samples via seek table
- **Custom player:** Implement buffering strategy around block indices

Let me know what your player is, and I'll provide step-by-step integration code! 🎬
