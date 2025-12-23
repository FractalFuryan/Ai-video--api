# container/seek.py
"""
Seek table: O(log n) time-based navigation.

Maps PTS -> file offset for fast random access without scanning.
Works with any opaque block format (audio, video, control, etc).
"""

from __future__ import annotations

import bisect
import struct
from typing import List, Optional, Tuple


class SeekEntry:
    """Single seek point: (PTS, byte offset)."""

    def __init__(self, pts: int, offset: int):
        self.pts = pts
        self.offset = offset

    def __repr__(self) -> str:
        return f"SeekEntry(pts={self.pts}, offset={self.offset})"

    def __eq__(self, other):
        if isinstance(other, tuple):
            return (self.pts, self.offset) == other
        return self.pts == other.pts and self.offset == other.offset

    def __lt__(self, other):
        if isinstance(other, tuple):
            return self.pts < other[0]
        return self.pts < other.pts


class SeekTable:
    """
    Binary-searchable seek table.

    Maintains sorted list of (PTS, offset) for fast lookups.
    """

    def __init__(self):
        self.entries: List[SeekEntry] = []
        self._finalized = False

    def add(self, pts: int, offset: int) -> None:
        """
        Add a seek point.

        Args:
            pts: Presentation timestamp.
            offset: Byte offset in stream/file.

        Raises:
            RuntimeError: If table already finalized.
        """
        if self._finalized:
            raise RuntimeError("seek table is finalized; cannot add")
        self.entries.append(SeekEntry(pts, offset))

    def finalize(self) -> None:
        """
        Sort and lock the table.

        Must call before seeking.
        """
        if not self._finalized:
            self.entries.sort(key=lambda e: e.pts)
            self._finalized = True

    def seek(self, pts: int) -> Optional[SeekEntry]:
        """
        Find the seek entry at or before a given PTS.

        Binary search: O(log n).

        Args:
            pts: Target presentation timestamp.

        Returns:
            Closest SeekEntry with pts <= target, or None.
        """
        if not self._finalized:
            raise RuntimeError("seek table not finalized")

        if not self.entries:
            return None

        # Binary search for rightmost entry with pts <= target
        lo, hi = 0, len(self.entries) - 1
        best_idx = -1
        while lo <= hi:
            mid = (lo + hi) // 2
            if self.entries[mid].pts <= pts:
                best_idx = mid
                lo = mid + 1
            else:
                hi = mid - 1

        if best_idx >= 0:
            return self.entries[best_idx]
        return None

    def serialize(self) -> bytes:
        """
        Binary format for storage.

        Format:
          "SEEK" magic (4)
          count u32 (4)
          [entry: pts u64 (8) + offset u64 (8)] * count
        """
        if not self._finalized:
            self.finalize()

        data = b"SEEK"
        data += struct.pack("<I", len(self.entries))
        for entry in self.entries:
            data += struct.pack("<QQ", entry.pts, entry.offset)
        return data

    @classmethod
    def deserialize(cls, data: bytes) -> SeekTable:
        """Reconstruct SeekTable from binary."""
        if data[:4] != b"SEEK":
            raise ValueError("invalid seek table magic")

        count = struct.unpack("<I", data[4:8])[0]
        table = cls()
        for i in range(count):
            offset = 8 + i * 16
            pts, off = struct.unpack("<QQ", data[offset : offset + 16])
            table.add(int(pts), int(off))
        table.finalize()
        return table

    def to_list(self) -> List[Tuple[int, int]]:
        """Export as [(pts, offset), ...] for API responses."""
        return [(e.pts, e.offset) for e in self.entries]

    def __len__(self) -> int:
        return len(self.entries)

    def __repr__(self) -> str:
        return f"SeekTable({len(self.entries)} entries)"
