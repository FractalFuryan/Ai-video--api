# adapters/null.py
"""
Null adapter: identity passthrough (for testing + fuzzing).

Useful for:
  - Verifying container round-trip integrity.
  - Benchmarking decode chain overhead (without model).
  - Fuzzing H4MK parsing without a real model.
"""

from __future__ import annotations

from typing import Any, Dict

from .base import DecodeState, ModelAdapter


class NullState(DecodeState):
    """Opaque null state: just accumulates block payloads."""

    def __init__(self):
        self.blocks: list[bytes] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "NullState",
            "block_count": len(self.blocks),
            "total_bytes": sum(len(b) for b in self.blocks),
        }


class NullAdapter(ModelAdapter):
    """
    No-op adapter: passes through opaque data unchanged.
    
    Output: concatenated byte buffer (all opaque payloads).
    """

    def decode_I(self, opaque: bytes) -> NullState:
        state = NullState()
        state.blocks.append(opaque)
        return state

    def apply_P(self, state: NullState, opaque: bytes) -> NullState:
        state.blocks.append(opaque)
        return state

    def finalize(self, state: NullState) -> bytes:
        """Concatenate all blocks."""
        return b"".join(state.blocks)
