"""HarmonyØ4 SeekTable Module Tests

Tests for O(log n) binary search seeking.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from container.seek import SeekTable


def test_seek_table_creation():
    """Create and populate seek table."""
    st = SeekTable()
    st.add(0, 0)
    st.add(33000, 65536)
    st.add(66000, 131072)
    st.finalize()
    
    assert len(st.entries) == 3


def test_seek_lookup():
    """Binary search lookup."""
    st = SeekTable()
    st.add(0, 0)
    st.add(33000, 65536)
    st.add(66000, 131072)
    st.finalize()
    
    # Seek to 0 returns first entry
    result = st.lookup(0)
    assert result == (0, 0)
    
    # Seek to 33000 returns exact match
    result = st.lookup(33000)
    assert result == (33000, 65536)
    
    # Seek to 50000 returns entry before it (33000)
    result = st.lookup(50000)
    assert result == (33000, 65536)
    
    # Seek to 100000 returns last entry before it
    result = st.lookup(100000)
    assert result == (66000, 131072)


def test_seek_table_serialization():
    """Serialize and deserialize seek table."""
    st = SeekTable()
    st.add(0, 0)
    st.add(33000, 65536)
    st.add(66000, 131072)
    st.finalize()
    
    serialized = st.serialize()
    assert isinstance(serialized, bytes)
    
    st2 = SeekTable.deserialize(serialized)
    assert len(st2.entries) == 3
    
    # Verify lookups work the same
    assert st.lookup(50000) == st2.lookup(50000)


if __name__ == "__main__":
    test_seek_table_creation()
    test_seek_lookup()
    test_seek_table_serialization()
    print("✅ All seek tests passed")
