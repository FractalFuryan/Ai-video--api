# Harmony4 Media: Multi-Track Container + Model-Agnostic Decode

A **production-ready, geometry-first** container format for audio/media with:

- ✅ **Multi-track GOP** (I/P/B blocks, per-track seek tables)
- ✅ **Model-agnostic payload routing** (opaque blobs, no secret leakage)
- ✅ **Deterministic random access** (seek tables, bounded decode chains)
- ✅ **Zero ML dependency** (pure geometry + CRC validation)
- ✅ **Drop-in container/adapter pattern** (Docker/GitHub ready)

---

## Architecture

### 1. **H4MK Container Format** (`harmony4_media/mux/`)

A simple, chunk-based layout:

```
[H4MK HEADER (16B)]
  [TRAK] Track definitions (JSON)
  [META] Metadata (JSON)
  [SAFE] Safety info (JSON)
  [VERI] Verification (JSON)
  [NOTE] Notes (text)
  [CORE] Opaque audio block (repeated)
  [CORE] ...
  [TSEK] Track 1 seek table
  [TSEK] Track 2 seek table
[CONTAINER CRC (4B)]
```

**Why this design:**
- Tracks are **inspectable** (JSON metadata).
- CORE payloads are **opaque** (no model leakage).
- Seek tables are **per-track** (independent access).
- CRC per chunk + container (integrity verified).

### 2. **GOP Flags** (`harmony4_media/mux/gop_flags.py`)

Compact u32 encoding:

```
bits 0..27  = PTS (milliseconds, ~74.6 hours max)
bits 28..29 = Block type (I/P/B)
bits 30..31 = Reserved
```

Enables **deterministic timing** without external metadata.

### 3. **Model Adapters** (`adapters/`)

Universal decode interface:

```python
class ModelAdapter(ABC):
    def decode_I(self, opaque: bytes) -> DecodeState: ...     # Keyframe
    def apply_P(self, state, opaque: bytes) -> DecodeState: ... # Predictive
    def apply_B(self, prev, next, opaque) -> DecodeState: ...  # Bidirectional (optional)
    def finalize(self, state) -> Any: ...                      # Output
```

Any model plugs in by implementing this interface.

---

## Quick Start

### Build a Container

```python
from harmony4_media.mux import mux_multitrack_gop, TrackSpec, Block, BLK_I, BLK_P

tracks = [
    TrackSpec(
        track_id=1,
        name="main",
        kind="audio",
        codec="h4core",  # Your closed codec
        sample_rate=48000,
        channels=1,
    )
]

blocks = {
    1: [
        Block(pts_ms=0, blk_type=BLK_I, opaque_blob=b"...keyframe..."),
        Block(pts_ms=33, blk_type=BLK_P, opaque_blob=b"...update..."),
    ]
}

container = mux_multitrack_gop(tracks, blocks)
open("audio.h4mk", "wb").write(container)
```

### Decode a Time Range

```python
from harmony4_media.mux import get_decode_chain, extract, unwrap_core_payload
from adapters.null import NullAdapter

container = open("audio.h4mk", "rb").read()
adapter = NullAdapter()

# Get decode chain for 100ms
chain = get_decode_chain(container, track_id=1, t_ms=100)

state = None
for chunk_idx in chain:
    payload = extract(container, chunk_idx)
    track_id, opaque = unwrap_core_payload(payload)
    
    if state is None:
        state = adapter.decode_I(opaque)
    else:
        state = adapter.apply_P(state, opaque)

output = adapter.finalize(state)
```

### CLI

```bash
# Build a demo container
python3 -m harmony4_media.cli mt_build --out my.h4mk

# List tracks and blocks
python3 -m harmony4_media.cli mt_list --in my.h4mk

# Compute decode chain
python3 -m harmony4_media.cli mt_chain --in my.h4mk --track 1 --t_ms 5000
```

---

## Module Structure

```
harmony4_media/
├── mux/
│   ├── h4mk.py              # Core container (mux/parse/extract)
│   ├── gop_flags.py         # Timing + block type encoding
│   └── h4mk_multitrack.py   # Multi-track + seek tables
├── cli.py                   # Command-line tools
└── __init__.py

adapters/
├── base.py                  # Abstract ModelAdapter + DecodeState
├── null.py                  # Identity passthrough (testing)
├── dsp.py                   # Freq-domain synthesis stub
└── __init__.py

examples/
└── build_and_decode.py      # End-to-end walkthrough
```

---

## How It Works (Technical)

### Multi-Track Routing

CORE blocks include a **routing header**:

```python
def wrap_core_payload(track_id: int, opaque_blob: bytes) -> bytes:
    return b"H4TB" + struct.pack("<HH", track_id, 0) + opaque_blob
```

The container **never interprets** `opaque_blob`; it only routes by `track_id`.

### Decode Chains (Bounded)

```python
def get_decode_chain(container, track_id, t_ms) -> List[int]:
    # 1. Find nearest I-block <= t_ms
    i_idx = find_keyframe_for_time(container, track_id, t_ms)
    
    # 2. Collect P/B blocks up to t_ms
    # 3. Stop at next I-block (GOP boundary)
    return [i_idx, ...P blocks..., ...B blocks...]
```

**Why this matters:**
- No unbounded dependencies (B-frames are optional).
- Random access always starts at I-block.
- Seek tables accelerate keyframe lookup (binary search).

### Seek Tables

Per-track binary index:

```
[H4TS magic (4)]
[track_id u16]
[entry_count u16]
[(pts_ms u32, chunk_idx u32) * count]
```

Enables **O(log n)** keyframe lookup instead of linear scan.

---

## Adapters by Example

### NullAdapter (Testing)

```python
from adapters.null import NullAdapter

adapter = NullAdapter()
# Concatenates all blocks; useful for:
#   - Container round-trip verification
#   - Fuzzing H4MK parsing
#   - Benchmarking without a model
```

### DSPAdapter (Synthesis Stub)

```python
from adapters.dsp import DSPAdapter

adapter = DSPAdapter(sample_rate=48000)
# Maintains frequency bins; apply_P updates deltas
# finalize() would do inverse-FFT (stub here)
```

### Your Model

```python
from adapters.base import ModelAdapter, DecodeState

class MyModelState(DecodeState):
    def __init__(self):
        self.hidden = ...  # Your model state
    def to_dict(self):
        return {"type": "MyModelState", ...}

class MyAdapter(ModelAdapter):
    def decode_I(self, opaque):
        # Parse opaque -> your format
        # Initialize model from keyframe
        return MyModelState(...)
    
    def apply_P(self, state, opaque):
        # Apply delta to state
        return state
    
    def finalize(self, state):
        # Convert state -> output (audio samples, etc)
        return ...
```

---

## Why This Design? 🧠

| Goal | Solution |
|------|----------|
| **Geometry-first** | GOP (I/P/B) + timing, no ML assumptions |
| **Model-agnostic** | Opaque blobs + adapter pattern |
| **Inspectable** | JSON metadata, no secrets in CORE |
| **Random access** | Seek tables + bounded decode chains |
| **Deterministic** | CRC validation, no floating-point state |
| **Scalable** | Per-track multiplexing, independent codecs |

---

## Testing

```bash
# Run end-to-end example
python3 examples/build_and_decode.py

# Build + inspect + decode via CLI
python3 -m harmony4_media.cli mt_build --out test.h4mk
python3 -m harmony4_media.cli mt_list --in test.h4mk
python3 -m harmony4_media.cli mt_chain --in test.h4mk --track 1 --t_ms 100
```

---

## Next: Extensions (Say the Word)

- **Token coherence scoring**: Cross-block quality metrics
- **Bind to SEEK tables**: Predictive prefetching
- **Encryption masks**: Per-token-block AES-GCM
- **Streaming ingest**: Chunked writes with incremental seek table
- **Cross-modal**: Image/video adapters (same interface)
- **Real-time RT-Audio**: Synthesis adapters + async decode

---

## Production Checklist

- ✅ Container format (versioned, CRC'd)
- ✅ Multi-track routing (opaque payloads)
- ✅ Seek tables (binary, per-track)
- ✅ Adapter pattern (model-agnostic)
- ✅ CLI tools (inspect + decode)
- ⬜ Performance (async decode, streaming)
- ⬜ Encryption (per-block, optional)
- ⬜ Compression (payload-level, optional)

---

**Built for production.** No secrets. No leakage. Fully inspectable. 🔒🚀
