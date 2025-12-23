# adapters/base.py
"""
Model adapter base: universal decode interface.

Any model/synth plugs in by implementing:
  - decode_I(opaque): init decode state from keyframe
  - apply_P(state, opaque): update state with predictive block
  - apply_B(prev_state, next_state, opaque): optional, for B-frames

The container supplies opaque blobs; the adapter interprets them.
No model knows about H4MK structure.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class DecodeState(ABC):
    """
    Opaque decode state (model-specific).
    
    A model adapter maintains this across blocks in a decode chain.
    """

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialize state for inspection/debugging."""
        ...


class ModelAdapter(ABC):
    """
    Universal model decode interface.
    
    Adapts a model/synth to H4MK decode chains.
    """

    @abstractmethod
    def decode_I(self, opaque: bytes) -> DecodeState:
        """
        Initialize decode from an I-block (keyframe).
        
        Args:
            opaque: Raw I-block payload from container.
        
        Returns:
            Initial decode state (no previous dependencies).
        """
        ...

    @abstractmethod
    def apply_P(self, state: DecodeState, opaque: bytes) -> DecodeState:
        """
        Apply a P-block (predictive, depends on previous state).
        
        Args:
            state: Current decode state (from prior I or P).
            opaque: Raw P-block payload from container.
        
        Returns:
            Updated decode state.
        """
        ...

    def apply_B(
        self, prev_state: DecodeState, next_state: DecodeState, opaque: bytes
    ) -> DecodeState:
        """
        Apply a B-block (bidirectional, depends on prior + future).
        
        This is optional and defaults to treating B as a variant of P.
        Subclasses can override for true bi-frame decoding.
        
        Args:
            prev_state: Decode state before this block.
            next_state: Decode state after this block (lookahead).
            opaque: Raw B-block payload from container.
        
        Returns:
            Updated decode state.
        """
        # Default: treat B like P (ignore future)
        return self.apply_P(prev_state, opaque)

    @abstractmethod
    def finalize(self, state: DecodeState) -> Any:
        """
        Convert final decode state to output (e.g., audio samples, control data).
        
        Args:
            state: Final decode state after chain.
        
        Returns:
            Model-specific output.
        """
        ...
