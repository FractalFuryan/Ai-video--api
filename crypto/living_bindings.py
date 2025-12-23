"""
Living Cipher bindings: encrypt CORE blocks with context binding.

Prevents block transplantation across containers via AAD (Additional Authenticated Data).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple
import hashlib

from crypto.living_cipher import LivingState, encrypt, decrypt


def sha256_hex(b: bytes) -> str:
    """SHA256 hash as hex string."""
    return hashlib.sha256(b).hexdigest()


@dataclass(frozen=True)
class CoreContext:
    """Context for binding a CORE block to a specific container + track + timestamp."""
    engine_id: str               # Compression engine ID
    engine_fp: str               # Engine fingerprint
    container_veri_hex: str      # Container VERI hash (hex)
    track_id: str                # Track ID
    pts_us: int                  # Timestamp
    chunk_index: int             # Index in CORE chunks

    def aad(self) -> bytes:
        """Generate AAD (Additional Authenticated Data) for this context."""
        # Bind block to container + track + timestamp, prevents transplant/replay
        s = f"H4MK|{self.engine_id}|{self.engine_fp}|{self.container_veri_hex}|{self.track_id}|{self.pts_us}|{self.chunk_index}"
        return s.encode("utf-8")


def encrypt_core_block(
    state: LivingState,
    payload: bytes,
    ctx: CoreContext,
) -> Tuple[bytes, bytes]:
    """
    Encrypt a CORE block with living cipher.
    Returns (header, ciphertext).
    """
    return encrypt(state, payload, aad=ctx.aad())


def decrypt_core_block(
    state: LivingState,
    header: bytes,
    ciphertext: bytes,
    ctx: CoreContext,
) -> bytes:
    """
    Decrypt a CORE block with living cipher.
    Raises if AAD doesn't match (block transplanted or context tampered).
    """
    return decrypt(state, header, ciphertext, aad=ctx.aad())
