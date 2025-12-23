# H4MK Container Format Specification

**Version**: 1.0  
**Status**: Production  
**Language**: Binary (little-endian)

---

## Overview

H4MK (Harmony 4 Media Kernel) is a deterministic, chunk-based container format designed for:
- Multi-track audio/media storage
- Per-track GOP (I/P/B) blocks with bounded decode chains
- Model-agnostic opaque payload routing
- Zero-copy random access via seek tables
- Full CRC validation at chunk + container level

---

## File Layout

```
[H4MK HEADER (16 bytes)]
[CHUNK 0]
[CHUNK 1]
...
[CHUNK N]
[CONTAINER CHECKSUM (4 bytes)]
```

---

## Header (16 bytes)

```
Offset  Size   Type   Description
------  ----   ----   -----------
0       4      bytes  Magic: "H4MK" (0x484D4B = big-endian ASCII)
4       1      u8     Version (currently 1)
5       1      u8     Flags (reserved, currently 0)
6       2      u16    Reserved (little-endian, currently 0)
8       8      u64    Timestamp (unix epoch, milliseconds; little-endian)
```

**Example**: `48 4D 4B 00 01 00 00 00 80 1A 06 00 00 00 00 00`

---

## Chunk Format

```
[CHUNK HEADER (12 bytes)]
[PAYLOAD (variable)]
[CRC32 (4 bytes)]
```

### Chunk Header (12 bytes)

```
Offset  Size   Type   Description
------  ----   ----   -----------
0       4      bytes  Type tag (e.g., "CORE", "META", "TRAK")
4       4      u32    Flags (meaning depends on type; little-endian)
8       4      u32    Payload length in bytes (little-endian)
```

### Chunk Payload (variable)

Opaque data; meaning depends on chunk type.

### Chunk Checksum (4 bytes)

CRC32 (little-endian) of header + payload. Detects corruption.

---

## Container Checksum (4 bytes)

CRC32 (little-endian) of entire file excluding this final 4 bytes.

---

## Chunk Types

### TRAK (Track Header)

**Type**: `54 52 41 4B`  
**Flags**: 0 (reserved)  
**Payload**: JSON object

```json
{
  "tracks": [
    {
      "track_id": 1,
      "name": "main",
      "kind": "audio",
      "codec": "h4core",
      "sample_rate": 48000,
      "channels": 2,
      "note": "Primary audio"
    }
  ]
}
```

### CORE (Opaque Block)

**Type**: `43 4F 52 45`  
**Flags**: `flags u32` where:
- bits 0..27: PTS milliseconds
- bits 28..29: block type (0=I, 1=P, 2=B)
- bits 30..31: reserved

**Payload**: Track-routed opaque blob

```
Offset  Size   Type   Description
------  ----   ----   -----------
0       4      bytes  Magic: "H4TB" (track-bound)
4       2      u16    Track ID (little-endian)
6       2      u16    Reserved (little-endian)
8       N      bytes  Opaque model payload
```

### META (Metadata)

**Type**: `4D 45 54 41`  
**Flags**: 0 (reserved)  
**Payload**: JSON object (global metadata)

```json
{
  "title": "Audio Demo",
  "duration_ms": 5000,
  "created_by": "harmony4_encoder v1.0"
}
```

### SAFE (Safety/Audit)

**Type**: `53 41 46 45`  
**Flags**: 0 (reserved)  
**Payload**: JSON object

```json
{
  "no_identity": true,
  "clearance": "internal",
  "audit_level": "strict"
}
```

### VERI (Verification)

**Type**: `56 45 52 49`  
**Flags**: 0 (reserved)  
**Payload**: JSON object

```json
{
  "sha256": "abc123...",
  "format_version": 1,
  "codec_version": "h4core.1"
}
```

### NOTE (Notes/Annotations)

**Type**: `4E 4F 54 45`  
**Flags**: 0 (reserved)  
**Payload**: Plain text (UTF-8)

```
This is a test encoding.
Produced by encoder v1.0.
For internal use only.
```

### TSEK (Track Seek Table)

**Type**: `54 53 45 4B`  
**Flags**: 0 (reserved)  
**Payload**: Binary seek index

```
Offset  Size   Type   Description
------  ----   ----   -----------
0       4      bytes  Magic: "H4SK"
4       2      u16    Track ID (little-endian)
6       2      u16    Reserved (little-endian)
8       4      u32    Entry count (little-endian)
12+     8*N    bytes  Entries (little-endian)
```

Each entry:
```
Offset  Size   Type   Description
------  ----   ----   -----------
0       4      u32    PTS milliseconds
4       4      u32    CORE chunk index (byte offset in payload)
```

---

## GOP Flags (u32)

Used in CORE chunks to encode timing + block type.

```
Bit Range  Description
----------  -----------
0..27      PTS milliseconds (0 to 268,435,455; ~74.6 hours)
28..29     Block type
           00 = I-frame (Intra, keyframe, no dependencies)
           01 = P-frame (Predictive, depends on prior I or P)
           10 = B-frame (Bidirectional, depends on prior + future)
           11 = Reserved
30..31     Reserved (must be 0)
```

**Example parsing**:
```python
flags = 0x03DA00B5  # 16-bit representation
pts_ms = flags & 0x0FFFFFFF  # bits 0..27
blk_type = (flags >> 28) & 0b11  # bits 28..29
```

---

## Example Container (Hex Dump)

```
Offset  Data
------  ----
0x00    48 4D 4B 00  01 00 00 00  80 1A 06 00  00 00 00 00  [H4MK header]
0x10    54 52 41 4B  00 00 00 00  4E 00 00 00  [TRAK chunk header, 78B payload]
0x1C    7B 22 74 72  61 63 6B 73  22 3A 5B 7B  [...JSON track metadata...]
...
0xAA    [CRC32 of TRAK chunk]
0xAE    43 4F 52 45  B5 00 DA 03  1C 00 00 00  [CORE chunk header, 28B payload, PTS=1000ms, type=I]
0xBA    48 34 54 42  01 00 00 00  [H4TB magic, track_id=1]
0xC2    ...opaque model blob...
...
```

---

## Parsing Algorithm (Pseudocode)

```python
def parse_h4mk(data: bytes):
    pos = 0
    
    # Read header
    magic = data[0:4]
    version = data[4]
    flags = data[5]
    timestamp = unpack_u64(data[8:16])
    
    pos = 16
    chunks = []
    
    # Read chunks until final CRC
    while pos < len(data) - 4:
        ctype = data[pos:pos+4]
        chunk_flags = unpack_u32(data[pos+4:pos+8])
        payload_len = unpack_u32(data[pos+8:pos+12])
        
        payload = data[pos+12:pos+12+payload_len]
        crc_pos = pos + 12 + payload_len
        stored_crc = unpack_u32(data[crc_pos:crc_pos+4])
        
        # Compute CRC
        chunk_data = data[pos:pos+12] + payload
        computed_crc = crc32(chunk_data)
        
        assert computed_crc == stored_crc, "Chunk CRC mismatch"
        
        chunks.append({
            'type': ctype,
            'flags': chunk_flags,
            'payload': payload,
        })
        
        pos = crc_pos + 4
    
    # Verify container CRC
    stored_container_crc = unpack_u32(data[-4:])
    computed_container_crc = crc32(data[:-4])
    assert computed_container_crc == stored_container_crc
    
    return chunks
```

---

## Decode Chain Computation

Given a container, track_id, and target time t_ms:

1. **Find keyframe**: Binary search TSEK for track_id, locate I-block at or before t_ms
2. **Collect blocks**: Starting from I-block, include subsequent P/B blocks up to t_ms
3. **Stop at boundary**: Halt when encountering next I-block (next GOP)
4. **Return indices**: Ordered list of CORE chunk indices to decode

**Pseudocode**:
```python
def get_decode_chain(container, track_id, t_ms):
    # Find keyframe using seek table
    i_block_idx = binary_search_seek_table(container, track_id, t_ms)
    
    if i_block_idx is None:
        return []
    
    chain = [i_block_idx]
    
    # Collect subsequent blocks
    for chunk in chunks_after(i_block_idx):
        if chunk.type != "CORE":
            continue
        pts, blk_type = parse_flags(chunk.flags)
        if pts > t_ms:
            break
        if blk_type == BLK_I:
            break  # Next GOP
        chain.append(chunk)
    
    return chain
```

---

## Size Estimation

For N tracks, M blocks per track, average payload P bytes:

```
Header:               16 bytes
Tracks metadata:      ~500 bytes (JSON, per-track)
Global sidecars:      ~1000 bytes (META, SAFE, VERI, NOTE)
CORE blocks:          M * (12 + P + 4) bytes per block
Seek tables:          ~(M/8) * 12 bytes per track (assuming keyframes every 8 blocks)
Container CRC:        4 bytes

Total ≈ 1.5KB + (M * (P + 16))
```

**Example**: 2 tracks, 1000 blocks, 100B avg payload = ~118KB

---

## Production Checklist

- ✅ Format versioning (field in header)
- ✅ CRC validation (chunk + container level)
- ✅ Deterministic chunk ordering (sortable by type + time)
- ✅ No floating-point (all u32/u64 integers)
- ✅ Zero-copy random access (seek tables)
- ✅ Model-agnostic payloads (opaque blobs)
- ✅ Inspectable metadata (JSON)
- ✅ Bounded decode chains (GOP boundaries)

---

**Format is production-ready. Use with confidence. 🔒🚀**
