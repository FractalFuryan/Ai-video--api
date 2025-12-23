# adapters/__init__.py
"""
Model adapters: universal decode interface for H4MK containers.

Core abstraction:
  - ModelAdapter: abstract base (decode_I, apply_P, apply_B, finalize)
  - DecodeState: opaque model state across blocks

Implementations:
  - NullAdapter: identity passthrough (testing)
  - DSPAdapter: frequency-domain synthesis stub
  - (Add TorchAdapter, YourModelAdapter, etc. as needed)

Usage pattern:

    from harmony4_media.mux import get_decode_chain, extract
    from adapters.null import NullAdapter

    # Load model
    adapter = NullAdapter()

    # Extract and decode a time range
    container = open("file.h4mk", "rb").read()
    chain = get_decode_chain(container, track_id=1, t_ms=5000)
    
    state = None
    for chunk_idx in chain:
        payload = extract(container, chunk_idx)
        track_id, opaque = unwrap_core_payload(payload)
        
        if state is None:
            state = adapter.decode_I(opaque)  # I-block
        else:
            state = adapter.apply_P(state, opaque)  # P-block

    output = adapter.finalize(state)
"""

from .base import DecodeState, ModelAdapter
from .null import NullAdapter, NullState
from .dsp import DSPAdapter, DSPState

__all__ = [
    "DecodeState",
    "ModelAdapter",
    "NullAdapter",
    "NullState",
    "DSPAdapter",
    "DSPState",
]
