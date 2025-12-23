"""
Universal video adapter contract (ABC).
Codec/model/pixel-agnostic. Transport-only.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class BlockHeader:
    """Public metadata for any video block."""
    track_id: str
    pts_us: int           # Presentation timestamp in microseconds
    kind: str             # "I" (independent) | "P" (dependent) | "B" (bi-directional)
    index: int            # Sequential block index within track
    keyframe: bool        # Is this a keyframe / random access point?


class VideoAdapter(ABC):
    """
    Universal model/codec adapter contract for VIDEO transport.
    This codebase never defines pixels/frames; the adapter interprets opaque CORE blocks.
    
    All methods treat state as opaque bytestrings or objects.
    No pixel/tensor/identity semantics in this layer.
    """

    @abstractmethod
    def decode_I(self, header: BlockHeader, block: bytes) -> Any:
        """
        Decode an independent I-block into an internal state.
        I-blocks carry full information; no prior context required.
        """
        ...

    @abstractmethod
    def apply_P(self, state: Any, header: BlockHeader, block: bytes) -> Any:
        """
        Apply a delta P-block to an existing state.
        Requires the prior state.
        """
        ...

    def apply_B(self, prev_state: Any, next_state: Any, header: BlockHeader, block: bytes) -> Any:
        """
        Optional B-block support (bidirectional / interpolation).
        Falls back to NotImplementedError if not supported.
        """
        raise NotImplementedError("B-block not supported by this adapter")

    @abstractmethod
    def render(self, state: Any) -> bytes:
        """
        Render state into a deliverable output format.
        Could be:
        - raw frames bytes (not recommended)
        - encoded frame packet stream
        - latent dumps for downstream processing
        """
        ...


class OpaquePassThroughAdapter(VideoAdapter):
    """
    Default safe adapter: treats I as state bytes, P as append-only deltas, render returns state.
    Useful for testing transport pipeline without codec logic.
    
    Deterministic. No hidden side effects.
    """

    def decode_I(self, header: BlockHeader, block: bytes) -> bytes:
        """I-block is state."""
        return block

    def apply_P(self, state: bytes, header: BlockHeader, block: bytes) -> bytes:
        """P-block appends to state."""
        return state + block

    def apply_B(self, prev_state: bytes, next_state: bytes, header: BlockHeader, block: bytes) -> bytes:
        """B-block: interpolate by returning next_state (simple choice)."""
        return next_state

    def render(self, state: bytes) -> bytes:
        """Render state as-is."""
        return state
