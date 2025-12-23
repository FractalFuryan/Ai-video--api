# tokenizers/base.py
"""
Base token interface: unified across audio/video/control.

A Token is a **structural unit**, not a semantic one:
  - Time coordinate (PTS)
  - Block index
  - Optional metadata (keyframe flag, etc)

It encodes **timing + navigation**, nothing more.
No compression semantics. No model logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable


class Token(ABC):
    """Base token: serializable time-based unit."""

    @abstractmethod
    def serialize(self) -> bytes:
        """Convert to bytes for transport."""
        ...

    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """Return metadata dict for inspection."""
        ...


class Tokenizer(ABC):
    """Base tokenizer: opaque data -> structured tokens."""

    @abstractmethod
    def encode(self, data: Any) -> Iterable[Token]:
        """
        Encode data into tokens.

        Args:
            data: Raw bytes or structured input.

        Yields:
            Token instances.
        """
        ...

    @abstractmethod
    def decode(self, tokens: Iterable[Token]) -> Any:
        """
        Reconstruct data from tokens (if reversible).

        Args:
            tokens: Token iterable.

        Returns:
            Reconstructed data.
        """
        ...
