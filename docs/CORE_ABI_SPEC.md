# HarmonyØ4 Compression Core ABI Specification

**Purpose**: Allow a closed, production-grade compression core to be loaded dynamically while maintaining a stable, auditable interface.

**Status**: Production Ready  
**Version**: 1.0  
**Date**: December 23, 2025

---

## Overview

The HarmonyØ4 compression system uses a **two-tier architecture**:

1. **Open Reference** (`compression/geo_ref.py`) — Fully auditable, GitHub-safe, RLE+delta
2. **Binary Core** (external C library) — Optimized, proprietary, loaded dynamically

Both implement the same **stable Python API** (`CompressionEngine` ABC), so the entire system works identically with either engine.

---

## Library Loading

### Environment Variable

```bash
export HARMONY4_CORE_PATH=/path/to/libh4core.so
# or on macOS:
export HARMONY4_CORE_PATH=/path/to/libh4core.dylib
# or on Windows:
set HARMONY4_CORE_PATH=C:\path\to\libh4core.dll
```

### Python Loader

The [compression/loader.py](../compression/loader.py) module uses `ctypes` to load the library and call its functions.

```python
from compression import load_engine

engine = load_engine()
# Returns CoreCompression if HARMONY4_CORE_PATH is set and library loads
# Returns GeometricReferenceCompressor otherwise
```

---

## Required Exported Symbols

### 1. `h4_compress`

**Signature**:
```c
size_t h4_compress(const void* in_ptr, size_t in_len, void** out_ptr);
```

**Purpose**: Compress input bytes deterministically.

**Parameters**:
- `in_ptr` — Input buffer (read-only)
- `in_len` — Input buffer size in bytes
- `out_ptr` — Pointer to output buffer pointer (will be filled by callee)

**Return**:
- Size of output buffer in bytes
- Caller must free using `h4_free()`

**Determinism Requirement**:
- MUST be deterministic: `h4_compress(data, len, &out)` called twice with identical input MUST produce identical output bytes (byte-for-byte match)
- This is verified by the HarmonyØ4 test suite

**Example (C)**:
```c
const char* input = "hello world";
void* output = NULL;
size_t output_len = h4_compress(input, strlen(input), &output);
// use output[0..output_len-1]
h4_free(output);
```

---

### 2. `h4_decompress`

**Signature**:
```c
size_t h4_decompress(const void* in_ptr, size_t in_len, void** out_ptr);
```

**Purpose**: Decompress (or recover) bytes.

**Parameters**:
- `in_ptr` — Compressed buffer (read-only)
- `in_len` — Compressed buffer size in bytes
- `out_ptr` — Pointer to output buffer pointer (will be filled by callee)

**Return**:
- Size of output buffer in bytes
- Caller must free using `h4_free()`

**Reversibility Guarantee**:
- MUST be reversible: `decompress(compress(X)) == X` (byte-for-byte) for any input X
- All data MUST be recoverable (lossless)

**Example (C)**:
```c
const char* original = "hello world";
void* compressed = NULL;
size_t comp_len = h4_compress(original, strlen(original), &compressed);

void* recovered = NULL;
size_t rec_len = h4_decompress(compressed, comp_len, &recovered);

assert(rec_len == strlen(original));
assert(memcmp(recovered, original, rec_len) == 0);

h4_free(compressed);
h4_free(recovered);
```

---

### 3. `h4_free`

**Signature**:
```c
void h4_free(void* ptr);
```

**Purpose**: Free memory allocated by `h4_compress()` or `h4_decompress()`.

**Parameters**:
- `ptr` — Pointer returned from `h4_compress()` or `h4_decompress()`

**Behavior**:
- MUST safely handle NULL pointers (no-op)
- MUST free all heap memory associated with `ptr`

**Example (C)**:
```c
void* buf = NULL;
size_t len = h4_compress(input, input_len, &buf);
// ...use buf...
h4_free(buf);  // Safe; handles NULL gracefully
```

---

## Python ctypes Binding

The [compression/loader.py](../compression/loader.py) module wraps these functions using ctypes:

```python
import ctypes

class CoreCompression(CompressionEngine):
    def __init__(self, lib_path: str):
        self.lib = ctypes.CDLL(lib_path)
        
        # Define C function signatures
        self.lib.h4_compress.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_void_p)]
        self.lib.h4_compress.restype = ctypes.c_size_t
        
        self.lib.h4_decompress.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_void_p)]
        self.lib.h4_decompress.restype = ctypes.c_size_t
        
        self.lib.h4_free.argtypes = [ctypes.c_void_p]
        self.lib.h4_free.restype = None
    
    def compress(self, data: bytes) -> bytes:
        out_ptr = ctypes.c_void_p()
        size = self.lib.h4_compress(data, len(data), ctypes.byref(out_ptr))
        result = ctypes.string_at(out_ptr, size)
        self.lib.h4_free(out_ptr)
        return result
    
    def decompress(self, data: bytes) -> bytes:
        out_ptr = ctypes.c_void_p()
        size = self.lib.h4_decompress(data, len(data), ctypes.byref(out_ptr))
        result = ctypes.string_at(out_ptr, size)
        self.lib.h4_free(out_ptr)
        return result
```

---

## Constraints & Safety

### Identity Safety

The core compressor MUST **NOT** embed:
- Speaker identification features
- Video semantics or content fingerprints
- Synthesis-enabling parameters
- Any personally identifiable information (PII)

**Verification**: The core output must be structure-only (timing + coefficients, no semantic meaning).

### Determinism

The core MUST produce **identical output** for identical input every time, on every platform.

**Verification**: HarmonyØ4 test suite checks this automatically.

```python
# From tests/test_compression.py
compressor = load_engine()
result1 = compressor.compress(data)
result2 = compressor.compress(data)
assert result1 == result2  # Determinism verified
```

### Losslessness (Reversibility)

The core MUST support **perfect reconstruction** of original data.

```python
original = b"..."
compressed = compressor.compress(original)
recovered = compressor.decompress(compressed)
assert original == recovered  # Losslessness verified
```

---

## Error Handling

### Allocation Failures

If memory allocation fails inside the core:
- `h4_compress()` should return `0`
- `h4_decompress()` should return `0`
- `*out_ptr` may be undefined (caller should check return value)

### Corrupted Input

If `h4_decompress()` receives corrupted input:
- Return value may be unpredictable
- Recovered data may be garbage
- No null-pointer dereference or buffer overrun
- Optional: set `*out_ptr` to NULL on error

---

## Testing Requirements

Before deploying a binary core, verify:

1. **Determinism** (same input → same output always)
   ```python
   for i in range(100):
       assert compressor.compress(data) == expected
   ```

2. **Reversibility** (compress → decompress exact match)
   ```python
   assert compressor.decompress(compressor.compress(data)) == data
   ```

3. **Identity Safety** (no speaker/video features)
   - Run through HarmonyØ4 test suite
   - No model fingerprints
   - Structure only

4. **Memory Leaks** (all allocations freed)
   - Use valgrind or asan
   - Verify h4_free() is called correctly

5. **Platform Compatibility**
   - Test on Linux, macOS, Windows
   - Test on x86_64, ARM64
   - Verify endianness handling

---

## Deployment

### Docker

Mount binary core into container:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . /app
COPY core/libh4core.so /opt/harmonyø4/libh4core.so
ENV HARMONY4_CORE_PATH=/opt/harmonyø4/libh4core.so
RUN pip install -r requirements.txt
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0"]
```

### Docker Compose

```yaml
services:
  harmony4:
    build: .
    volumes:
      - ./core:/core:ro
    environment:
      - HARMONY4_CORE_PATH=/core/libh4core.so
```

### Fallback Behavior

If `HARMONY4_CORE_PATH` is not set or library fails to load:
- HarmonyØ4 automatically falls back to reference compressor
- Same API, same outputs (but reference is slower)
- Fully auditable

```python
engine = load_engine()
# If core unavailable, returns GeometricReferenceCompressor
# If core available, returns CoreCompression wrapper
# Caller doesn't need to know which
```

---

## Stability & Versioning

### API Stability

The Python interface (`compression.api.CompressionEngine`) is **frozen** and never changes.

Any new features must be backward-compatible or use environment variables.

### Core Versioning

The binary core ABI is also frozen. If you need to change the ABI:
- Keep old symbols for backward compatibility
- Add new symbols with versioned names: `h4_compress_v2`, etc.
- Update `HARMONY4_CORE_PATH` to select version

---

## Example Implementation (C stub)

Below is a **minimal reference implementation** to understand the ABI:

```c
#include <stdlib.h>
#include <string.h>

// Minimal RLE+delta compressor (reference only)
size_t h4_compress(const void* in_ptr, size_t in_len, void** out_ptr) {
    if (!in_ptr || !out_ptr) return 0;
    
    const unsigned char* in = (const unsigned char*)in_ptr;
    unsigned char* out = (unsigned char*)malloc(in_len * 2);  // Worst case
    if (!out) return 0;
    
    size_t out_idx = 0;
    for (size_t i = 0; i < in_len; i++) {
        out[out_idx++] = in[i];
        // RLE: repeat count
        size_t run = 1;
        while (i + run < in_len && in[i + run] == in[i] && run < 255) run++;
        out[out_idx++] = (unsigned char)run;
        i += run - 1;
    }
    
    *out_ptr = out;
    return out_idx;
}

size_t h4_decompress(const void* in_ptr, size_t in_len, void** out_ptr) {
    if (!in_ptr || !out_ptr) return 0;
    
    const unsigned char* in = (const unsigned char*)in_ptr;
    unsigned char* out = (unsigned char*)malloc(in_len * 2);  // Guess
    if (!out) return 0;
    
    size_t out_idx = 0;
    for (size_t i = 0; i < in_len; i += 2) {
        unsigned char val = in[i];
        unsigned char run = in[i + 1];
        for (size_t j = 0; j < run; j++) {
            out[out_idx++] = val;
        }
    }
    
    *out_ptr = out;
    return out_idx;
}

void h4_free(void* ptr) {
    free(ptr);
}
```

---

## Public Statement (Safe)

> *HarmonyØ4 supports optional binary compression cores that maintain the same deterministic, auditable interface as the open reference implementation. The core ABI is stable and publicly documented, allowing production deployments to optimize performance without changing the application code.*

---

## Questions?

For more info:
- Python loader: [compression/loader.py](../compression/loader.py)
- Reference impl: [compression/geo_ref.py](../compression/geo_ref.py)
- Tests: [tests/test_compression.py](../tests/test_compression.py)
- Architecture: [docs/COMPRESSION_ARCHITECTURE.md](./COMPRESSION_ARCHITECTURE.md)
