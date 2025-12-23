"""
HarmonyØ4 Crypto Module

Living Cipher: Forward-secure, tamper-evident ratcheting encryption.
- Out-of-order support (bounded cache)
- Periodic root ratchet (fresh X25519)
- Transcript binding (anti-tamper)
- Deterministic, auditable, privacy-preserving
"""

from crypto.living_cipher import (
    LivingState,
    init_from_shared_secret,
    encrypt,
    decrypt,
    sha256,
    hkdf,
)

__all__ = [
    "LivingState",
    "init_from_shared_secret",
    "encrypt",
    "decrypt",
    "sha256",
    "hkdf",
]
