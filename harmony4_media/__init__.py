# harmony4_media/__init__.py
"""
Harmony4 Media: unified tokenization + GOP container.

Modules:
  - mux: H4MK container format (multi-track, GOP, seek tables)
  - (future) tokenizers: audio/image/video frequency-domain
  - (future) adapters: model-specific decode shims
"""

from . import mux

__version__ = "0.1.0"

__all__ = ["mux"]
