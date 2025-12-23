---
title: HarmonyØ4 Compression Sealing Specification
---

# 🔐 Compression Sealing — Tamper-Evident & Attestable

**One-line guarantee:**
> HarmonyØ4 refuses to run with an unrecognized or altered compression core, and every container cryptographically binds the engine identity that produced it.

---

## Executive Summary

Compression in HarmonyØ4 is **sealed**: locked, verified, and tamper-evident.

| Property | Guarantee |
|----------|-----------|
| **No Silent Swaps** | Different cores produce different outputs → VERI mismatch |
| **No Downgrades** | Engine ID pinning prevents version downgrade attacks |
| **No Tampering** | Core fingerprint verification detects modifications |
| **No Leakage** | Safe public interface, zero algorithm disclosure |
| **Auditable** | Sealing info in metadata, verifiable without algorithm access |
| **Deterministic** | Same input always produces identical output |

---

## Architecture

### 1. Engine Sealing (Loader Layer)

**File:** `compression/loader.py` → `CoreCompression._verify_seals()`

When the binary core is loaded, HarmonyØ4 verifies:

#### Check 1: Engine ID
```
HARMONY4_ENGINE_ID env var vs. actual core
Example:
  Expected: h4core-geo-v1.2.3
  Found:    h4core-rle-v2.0.1
  → FAIL: Refuse to start
```

#### Check 2: Engine Fingerprint
```
HARMONY4_ENGINE_FP env var vs. SHA256(core binary)
Example:
  Expected: a7c4b1d9e2f0a3c5...
  Found:    f9e2c8d5b1a6f2c4...
  → FAIL: Refuse to start
```

**Effect:**
- ✅ Core can be updated only via explicit env vars
- ✅ Swapping cores requires environment change
- ✅ CI/CD gates prevent accidental mistakes

---

### 2. Container Sealing (Metadata)

**File:** `container/h4mk.py` → `build_h4mk()`

Sealing info is injected into every H4MK container's `META` chunk:

```json
{
  "compression": {
    "engine": "core",
    "engine_id": "h4core-geo-v1.2.3",
    "fingerprint": "a7c4b1d9e2f0a3c5...",
    "deterministic": true,
    "identity_safe": true,
    "opaque": true,
    "sealed": true
  }
}
```

**Non-sensitive:** All fields are public.
**Immutable:** Once VERI is computed, META is locked.
**Verifiable:** Auditors can see which engine produced this container.

---

### 3. Cryptographic Binding (VERI Chunk)

**File:** `container/h4mk.py` → `build_h4mk()`

VERI (SHA256) hash includes:
- All CORE chunks
- SEEK metadata
- **META** (with compression engine info)
- SAFE constraints

**Security property:**
```
Change compression engine → CORE bytes change
CORE bytes change → VERI mismatch
VERI mismatch → Container invalid
```

**Result:** Compression is now cryptographically bound to the container.

---

### 4. Runtime Attestation (Optional)

**File:** `compression/attest.py`

Generates live proof of which engine is active:

```python
from compression import attest

att = attest()
# Returns:
# {
#   "engine_id": "h4core-geo-v1.2.3",
#   "fingerprint": "a7c4b1d9...",
#   "timestamp_unix": 1703349600,
#   "attestation_hash": "e91d5c8b...",
#   "sealed": true
# }
```

**Use case:** Prove to auditors *right now* which core is active.
**Endpoint:** `GET /compress/attest`

---

## Deployment Checklist

### Setting Sealing Parameters

**Option 1: Strict Sealing (Recommended)**

```bash
export HARMONY4_CORE_PATH=/path/to/h4core.so
export HARMONY4_ENGINE_ID=h4core-geo-v1.2.3
export HARMONY4_ENGINE_FP=a7c4b1d9e2f0a3c5...
```

Process will:
- ✅ Load core
- ✅ Verify ID matches `h4core-geo-v1.2.3`
- ✅ Verify fingerprint matches expected
- ✅ Refuse to start if either check fails

**Option 2: Loose Sealing (ID only)**

```bash
export HARMONY4_CORE_PATH=/path/to/h4core.so
export HARMONY4_ENGINE_ID=h4core-geo-v1.2.3
```

Will:
- ✅ Load core
- ✅ Verify ID
- ⚠️ Skip fingerprint check (use if binary changes expected)

**Option 3: Reference Only (OSS/CI)**

```bash
# Don't set HARMONY4_CORE_PATH
```

Will:
- ✅ Load reference implementation
- ✅ Skip all seal checks
- ✅ Fully auditable (open source)

---

## API Endpoints

### GET /compress/info
Returns engine metadata + seal status:
```json
{
  "engine": "core",
  "engine_id": "h4core-geo-v1.2.3",
  "fingerprint": "a7c4b1d9...",
  "deterministic": true,
  "identity_safe": true,
  "opaque": true,
  "sealed": true
}
```

### GET /compress/attest
Returns live attestation:
```json
{
  "engine_id": "h4core-geo-v1.2.3",
  "fingerprint": "a7c4b1d9...",
  "timestamp_unix": 1703349600,
  "attestation_hash": "e91d5c8b...",
  "sealed": true,
  "engine": "core"
}
```

---

## Testing Sealing

### CI Guardrail Test

```python
def test_ci_guardrail_no_real_core():
    """CI should NOT have real compression core loaded."""
    if os.getenv("CI"):
        assert os.getenv("HARMONY4_CORE_PATH") is None
```

Prevents accidental leakage of proprietary core into GitHub.

### Seal Verification Test

```python
def test_sealing_info_in_metadata():
    """Sealing info must be present in container metadata."""
    h4mk = build_h4mk(...)
    reader = H4MKReader(h4mk)
    meta = json.loads(reader.get_chunks(b"META")[0])
    
    assert "compression" in meta
    assert "sealed" in meta["compression"]
    assert meta["compression"]["sealed"] is True
```

---

## Threat Model

### What Sealing Protects Against

| Attack | Prevention |
|--------|-----------|
| **Silent core swap** | Container VERI changes → detected |
| **Downgrade to older version** | Engine ID check → refused |
| **Core tampering** | Fingerprint check → refused |
| **Non-deterministic output** | Same input → same output guarantee |
| **Parameter leakage** | Public interface only, no secrets |

### What Sealing Does NOT Protect Against

| Issue | Mitigated By |
|-------|--------------|
| **Source code tampering** | Audits, code review, signing |
| **Supply chain attacks** | Binary verification, signed releases |
| **Key/secret leakage** | HSM-backed core (future) |
| **Side-channel attacks** | Constant-time implementation (future) |

---

## Advanced Usage

### Custom Sealing (Future)

#### Ed25519 Signing of H4MK

```python
# Sign entire container
from compression.seal import sign_h4mk, verify_h4mk_signature

h4mk = build_h4mk(...)
signature = sign_h4mk(h4mk, private_key)

# Later: verify
assert verify_h4mk_signature(h4mk, signature, public_key)
```

#### Keyed VERI (HMAC Mode)

```python
# For private pipelines
from compression.seal import build_h4mk_keyed

h4mk = build_h4mk_keyed(..., hmac_key=secret_key)
# VERI now includes HMAC(secret_key, container)
# Only systems with key can verify
```

---

## Example: Production Deployment

### Environment Setup

```bash
#!/bin/bash

# Load the sealed core
export HARMONY4_CORE_PATH=/opt/h4core/v1.2.3/h4core.so
export HARMONY4_ENGINE_ID=h4core-geo-v1.2.3
export HARMONY4_ENGINE_FP=a7c4b1d9e2f0a3c5d8f1b2c4e7f9a1d3

# Start API
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Verification

```bash
# Check which engine is active
curl http://localhost:8000/compress/info
# {
#   "engine": "core",
#   "engine_id": "h4core-geo-v1.2.3",
#   "fingerprint": "a7c4b1d9...",
#   "sealed": true
# }

# Get runtime attestation
curl http://localhost:8000/compress/attest
# {
#   "engine_id": "h4core-geo-v1.2.3",
#   "fingerprint": "a7c4b1d9...",
#   "timestamp_unix": 1703349600,
#   "attestation_hash": "e91d5c8b...",
#   "sealed": true
# }

# Compress and verify container is sealed
curl -X POST http://localhost:8000/compress \
  -F "file=@data.bin" > data.compressed

# Check container metadata
python3 -c "
from container.reader import H4MKReader
import json

data = open('data.h4mk', 'rb').read()
reader = H4MKReader(data)
meta = json.loads(reader.get_chunks(b'META')[0])
print(json.dumps(meta['compression'], indent=2))
"
# {
#   "engine": "core",
#   "engine_id": "h4core-geo-v1.2.3",
#   "sealed": true,
#   ...
# }
```

---

## Audit Checklist

- [ ] Binary core available and loadable
- [ ] `HARMONY4_CORE_PATH` set correctly
- [ ] `HARMONY4_ENGINE_ID` matches actual core version
- [ ] `HARMONY4_ENGINE_FP` matches actual core binary
- [ ] API /compress/info returns "sealed": true
- [ ] Sample containers have sealing info in META
- [ ] VERI chunks match metadata hashes
- [ ] CI environment does NOT set HARMONY4_CORE_PATH
- [ ] All test_sealing.py tests pass
- [ ] Attestation endpoint responds with current state

---

## Summary

🔒 **Sealing is active by default.** No configuration needed for reference engine.

🔐 **Production requires explicit sealing.** Set `HARMONY4_CORE_PATH`, `HARMONY4_ENGINE_ID`, `HARMONY4_ENGINE_FP`.

✅ **Tamper-evident guarantee:** Change compression → container invalid.

🔍 **Fully auditable:** Sealing info in public metadata, verifiable without algorithm access.

**Result:** HarmonyØ4 compression is locked, tracked, and verifiable. No silent swaps. No downgrades. No tampering.
