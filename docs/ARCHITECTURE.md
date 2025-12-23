# 🧱 HarmonyØ4 Architecture

**Document**: Complete technical architecture  
**Status**: ✅ LOCKED & PRODUCTION READY  
**Date**: December 22, 2025

---

## 🌀 Core Philosophy

HarmonyØ4 is built on **7 immutable principles**:

1. **Structure before meaning** — Never interpret content
2. **Time is explicit** — PTS markers on every token
3. **Determinism beats heuristics** — Same input = same output
4. **Transport ≠ synthesis** — No codec logic, no generation
5. **Auditability is non-optional** — Every operation reversible
6. **Safety by construction** — Cannot be used for deepfakes
7. **Containers are the contract** — H4MK is the single source of truth

---

## 🏗️ Tier Architecture (Hard Boundaries)

The codebase is organized as **4 independent tiers**, each with explicit responsibilities and forbidden operations:

```
┌──────────────────────────────────────┐
│  Tier 1: API Layer (FastAPI routes)  │  ← HTTP only
├──────────────────────────────────────┤
│ Tier 2: Transport (H4MK + seeking)   │  ← Container I/O
├──────────────────────────────────────┤
│ Tier 3: Tokenization (structure)     │  ← Media encoding
├──────────────────────────────────────┤
│ Tier 4: Utilities (crypto + hash)    │  ← Pure primitives
└──────────────────────────────────────┘
```

### Tier 4 — Utilities (`utils/`)

**Module Purpose**: Pure cryptographic and hashing primitives

**Files**:
- `crypto.py` — HKDF key derivation, XOR masking, MaskSpec config
- `hashing.py` — SHA256, CRC32 checksums

**Key Types**:
- `MaskSpec` — Transport encryption configuration
- No business logic, no media assumptions

**Dependencies**: External only (cryptography, hashlib, zlib)

**Forbidden**:
- ❌ Importing from tokenizers, container, or api
- ❌ Media interpretation
- ❌ Network I/O

---

### Tier 3 — Tokenization (`tokenizers/`)

**Module Purpose**: Structure-only media representations

**Files**:
- `base.py` — ABC interfaces (Token, Tokenizer)
- `video_transport.py` — VideoBlockToken (opaque blocks + PTS)
- `audio_fft.py` — AudioToken (FFT harmonics, frequency bins)
- `video.py` — Original VideoTokenizer (legacy, kept)

**Key Types**:
- `Token` — Base ABC with `metadata()` + `serialize()`
- `Tokenizer` — Base ABC with `encode()` + `decode()`
- `VideoBlockToken` — Opaque bytes + PTS + block index
- `AudioToken` — Frequency bins (real FFT output)

**Key Invariant**: Tokens are **non-identity** (cannot reconstruct original media from tokens alone)

**Dependencies**: numpy, utils tier

**Forbidden**:
- ❌ Storing to disk (container's job)
- ❌ Network I/O (api's job)
- ❌ Encryption (utils's job)

---

### Tier 2 — Transport Layer (`container/`)

**Module Purpose**: H4MK binary format + deterministic seeking

**Files**:
- `h4mk.py` — Container builder (CORE/META/SAFE/VERI chunks)
- `seek.py` — SeekTable with O(log n) binary search
- `chunks.py` — CoreChunk + ChunkStream routing
- `reader.py` — **NEW** — H4MK parser + chunk extraction

**H4MK Format**:
```
Magic:     4 bytes "H4MK"
Version:   4 bytes (1)
Chunks:    [tag(4B) + size(4B) + crc(4B) + payload]*

Chunk Tags:
  CORE   → Media payload (tokenized)
  SEEK   → SeekTable (PTS → offset mappings)
  META   → Duration, frame count, etc.
  SAFE   → Masked tokens (encrypted transport)
  VERI   → SHA256 hash of all above chunks
```

**SEEK Table** (O(log n) lookup):
```
Entry format: PTS (8B) + Offset (8B)
Binary search: largest PTS <= target_pts
```

**Key Types**:
- `H4MKBuilder` — Assemble CORE/META/SEEK/SAFE/VERI chunks
- `SeekTable` — Ordered list of (pts, offset) entries
- `SeekEntry` — Single keyframe entry
- `H4MKReader` — Parse H4MK file + extract chunks
- `ChunkInfo` — Metadata about single chunk (offset, size, CRC)

**Dependencies**: utils tier

**Forbidden**:
- ❌ Media semantics (pixel/audio interpretation)
- ❌ FFTs, codecs, synthesis
- ❌ API routing

---

### Tier 1 — API Layer (`api/`)

**Module Purpose**: HTTP routing + streaming endpoints

**Files**:
- `main.py` — FastAPI app initialization + lifespan
- `video.py` — /video/stream (SSE), /video/export (H4MK)
- `audio.py` — /audio/stream (SSE FFT), /audio/mask (XOR)
- `video_range.py` — **NEW** — /video/range (HTTP 206), /video/seek, /video/info

**Endpoints**:

| Path | Method | Purpose |
|------|--------|---------|
| `/video/stream` | POST | SSE stream tokens + metadata |
| `/video/export` | POST | Build H4MK + optional masking |
| `/video/range` | GET | HTTP 206 partial content + Range support |
| `/video/seek` | GET | Binary search SEEK table (O(log n)) |
| `/video/info` | GET | Inspect H4MK structure + metadata |
| `/audio/stream` | POST | SSE stream FFT tokens |
| `/audio/mask` | POST | Apply XOR transport encryption |
| `/health` | GET | Liveness probe |

**Key Types**:
- FastAPI routers
- Pydantic models for validation
- Response builders

**Dependencies**: All tiers (Tier 1 sits on top)

**Forbidden**:
- ❌ Crypto logic (use utils tier)
- ❌ Token math (use tokenizers tier)
- ❌ Container logic (use container tier)

---

## 📦 Extension: CLI Tool (`cli/`)

**Module Purpose**: Command-line interface for H4MK operations

**Files**:
- `main.py` — Entry point + subcommand dispatcher
- `__init__.py` — Package marker

**Commands**:
```bash
harmonyø4 inspect <file.h4mk>        # View structure + metadata
harmonyø4 seek <file.h4mk> <pts>     # Find keyframe at PTS
harmonyø4 export <input> -o <output> # Build H4MK container
```

**Integration**: pyproject.toml defines script entry point
```toml
[project.scripts]
harmonyø4 = "cli.main:main"
```

**Dependencies**: container tier (for H4MKReader)

---

## 🐳 Containerization

### Dockerfile

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . ./
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0"]
```

### docker-compose.yml

```yaml
version: "3.9"
services:
  harmonyø4:
    build: .
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
```

**One-command deployment**:
```bash
docker-compose up -d
```

---

## 📊 Dependency Graph

```
External libs (fastapi, numpy, cryptography)
         ↓
  Tier 4: utils/
    ├─ crypto.py
    └─ hashing.py
         ↓
  Tier 3: tokenizers/
    ├─ base.py
    ├─ video_transport.py
    └─ audio_fft.py
         ↓
  Tier 2: container/
    ├─ h4mk.py
    ├─ seek.py
    ├─ chunks.py
    └─ reader.py
         ↓
  Tier 1: api/
    ├─ main.py
    ├─ video.py
    ├─ audio.py
    └─ video_range.py
         ↓
    cli/ (parallel to api/)
    └─ main.py
```

**Key Property**: No circular dependencies. Clean downward flow only.

---

## 🧪 Test Organization

| Layer | Test File | Coverage |
|-------|-----------|----------|
| Tier 4 | `test_crypto.py` | HKDF, XOR, determinism |
| Tier 4 | `test_seek.py` | Binary search O(log n) |
| Tier 2 | `test_h4mk.py` | Container integrity |
| Tier 3 | `test_audio_api.py` | FFT tokenization |
| Tier 3 | `test_video_api.py` | Video tokenization |
| All | `test_harmony4_integration.py` | 6-suite end-to-end |

**Target**: 100% coverage on Tier 2–4, integration tests for Tier 1

---

## 🔄 Write Path (Tokenize → Container → Stream)

```
Raw frames/samples
      ↓
Tier 3: Tokenize (VideoTransportTokenizer / AudioFFTTokenizer)
      ↓
Token[] with PTS markers
      ↓
Tier 2: Container builder
      ├─ Assemble CORE chunk
      ├─ Build SEEK table
      ├─ Add META chunk
      ├─ Compute VERI hash
      └─ Output H4MK binary
      ↓
H4MK file (on disk or memory)
      ↓
Tier 1: API endpoint POST /video/export
      └─ Stream back to client
```

---

## 📖 Read Path (Parse → Seek → Stream)

```
H4MK file (hex-encoded in request)
      ↓
Tier 2: H4MKReader
      ├─ Parse magic + version
      ├─ Extract all chunks
      ├─ Verify CRCs
      └─ Build in-memory index
      ↓
ChunkInfo[] + SEEK table in memory
      ↓
Tier 1: API endpoint GET /video/seek
      ├─ Binary search SEEK table
      └─ Return keyframe entry
      ↓
Tier 1: API endpoint GET /video/range
      ├─ Parse HTTP Range header
      ├─ Extract byte slice from CORE
      └─ Return 206 Partial Content
```

---

## 🛡️ Transport Encryption Path (Optional)

```
Raw frames
      ↓
Tier 3: Tokenize
      ↓
Token[] (plaintext)
      ↓
Tier 1: POST /audio/mask (with master_key)
      ├─ Tier 4: Derive mask via HKDF(master_key, salt)
      ├─ Tier 4: XOR tokens with mask
      └─ Return masked tokens
      ↓
Masked tokens (deterministic, not encrypted!)
      ↓
Tier 2: Container builder (with masked tokens in SAFE chunk)
      ├─ SAFE chunk = masked version
      ├─ CORE chunk = plaintext (optional, for comparison)
      └─ VERI = hash of both
```

**Key Point**: Masking is **XOR-based, fully reversible**, and provides **transport security only**—not codec encryption.

---

## ⚡ Performance Model

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Tokenize 1 minute video | O(n) | Linear in frame count |
| Build H4MK | O(n) | Linear in token count |
| SEEK to PTS | O(log k) | k = number of keyframes |
| HTTP Range lookup | O(1) | Direct byte indexing |
| Verify CRC | O(n) | Linear in chunk size |
| XOR mask | O(n) | Linear in token count |

**Scalability**: Handles seconds → hours → multi-TB streams without architecture changes.

---

## 🌀 HarmonyØ4 as a System

**What it is**:
- ✅ Deterministic tokenization
- ✅ Provable seeking (O(log n))
- ✅ Auditable containers
- ✅ Transport-first security
- ✅ Safety by construction

**What it is NOT**:
- ❌ Codec (no compression)
- ❌ Model (no ML)
- ❌ Generator (no synthesis)
- ❌ Identity system (no biometrics)
- ❌ Encryption (only masked transport)

---

## 🔮 Future Extensions (Already Slotted)

These additions fit cleanly without refactoring:

1. **Signed Chunks** — ECDSA signature per chunk
   - File: `container/signer.py`
   - Dependency: cryptography lib

2. **Merkle-Verified SEEK** — Proof of correct ordering
   - File: `container/merkle.py`
   - Enables: Trustless seek verification

3. **Cross-Modal Bundles** — Audio + video side-by-side
   - File: `container/bundle.py`
   - Format: Multi-track H4MK variant

4. **HTTP Range Optimization** — Pre-computed range maps
   - File: `api/video_range_optimized.py`
   - Benefit: Millisecond seeks at scale

---

## 📚 Documentation Map

| Document | Purpose |
|----------|---------|
| [README.md](../README.md) | Project overview + quick start |
| [ARCHITECTURE.md](ARCHITECTURE.md) | This file — technical deep dive |
| [FINAL_SUMMARY.md](FINAL_SUMMARY.md) | Deployment checklist |
| [DEPLOYMENT_READY.md](DEPLOYMENT_READY.md) | Production setup guide |
| [HARMONY4_UPGRADE.md](HARMONY4_UPGRADE.md) | Complete spec |
| [QUICK_START_API.md](QUICK_START_API.md) | Code examples |

---

## ✨ Summary

HarmonyØ4 architecture is:

**Clean** — 4-tier separation with no circular deps  
**Safe** — Cannot be used for identity or synthesis  
**Fast** — O(log n) seeking on multi-TB streams  
**Auditable** — Every operation reversible + hashable  
**Extensible** — New features slot cleanly  
**Deterministic** — Bit-for-bit reproducible  

**Ready for production, audit, and scale.**

---

*Made 🔥 for systems that refuse to lie.*
