"""HarmonyØ4 H4MK Container Builder Tests

Tests for container assembly and structure.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from container.h4mk import build_h4mk, Chunk
from container.seek import SeekTable
from utils.crypto import sha256


def test_chunk_packing():
    """Chunk serialization with CRC32."""
    chunk = Chunk(b"TEST", b"hello")
    packed = chunk.pack()
    
    assert packed[:4] == b"TEST"
    assert len(packed) == 20  # TAG(4) + LEN(4) + CRC(4) + PAYLOAD(5) + padding
    

def test_h4mk_container_build():
    """Build complete H4MK container."""
    core_blocks = [b"frame_%d" % i for i in range(3)]
    
    seek = SeekTable()
    seek.add(0, 0)
    seek.add(33000, 100)
    seek.finalize()
    
    meta = {"project": "HarmonyO4", "fps": 30}
    safe = {"scope": "transport-only"}
    
    container = build_h4mk(core_blocks, seek.entries, meta, safe)
    
    # Verify H4MK header
    assert container[:4] == b"H4MK"
    assert len(container) > 100  # Minimum size


def test_h4mk_structure():
    """Verify H4MK structure with all chunks."""
    core = [b"data_%d" % i for i in range(2)]
    
    seek = SeekTable()
    seek.add(0, 0)
    seek.finalize()
    
    meta = {"project": "HarmonyO4"}
    safe = {"scope": "transport"}
    
    h4mk = build_h4mk(core, seek.entries, meta, safe)
    
    # Check magic and version
    assert h4mk[:4] == b"H4MK"
    version = int.from_bytes(h4mk[4:6], "big")
    assert version == 1
    
    # Container should have VERI chunk (last chunk)
    assert b"VERI" in h4mk


if __name__ == "__main__":
    test_chunk_packing()
    test_h4mk_container_build()
    test_h4mk_structure()
    print("✅ All H4MK tests passed")
