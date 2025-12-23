# tokenizers/__init__.py
"""
Unified tokenization layer: audio, video, control.

Core abstraction:
  - Token: serializable unit (time + metadata only, no meaning)
  - Tokenizer: encoder that produces tokens from opaque data

Pattern:
  Tokenizer.encode(data) -> Iterable[Token]
  token.serialize() -> bytes (for transport)

This keeps tokenization separate from transport and model logic.
"""

from .base import Token, Tokenizer

__all__ = ["Token", "Tokenizer"]
