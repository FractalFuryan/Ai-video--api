"""
HarmonyØ4 Living Cipher (v3)

A forward-secure, tamper-evident ratcheting cipher with:
- Out-of-order support (bounded skipped-key cache)
- Periodic root ratchet (fresh X25519 DH every M messages)
- Transcript binding (anti-reorder, anti-tamper)
- Binary-framed headers (no delimiter parsing bugs)
- Deterministic, auditable, privacy-preserving

No ML. Pure cryptography. Auditable by design.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict, Any
import hashlib
import struct

from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# For periodic root ratchet (fresh DH)
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

# ----------------------------
# Helpers
# ----------------------------


def sha256(b: bytes) -> bytes:
    """Deterministic SHA256 hash."""
    return hashlib.sha256(b).digest()


def hkdf(
    key_material: bytes,
    info: bytes,
    length: int = 32,
    salt: Optional[bytes] = None,
) -> bytes:
    """HKDF-SHA256 key derivation."""
    return HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        info=info,
    ).derive(key_material)


def u64(n: int) -> bytes:
    """Encode u64 big-endian."""
    return struct.pack(">Q", n)


def read_u64(b: bytes) -> int:
    """Decode u64 big-endian."""
    return struct.unpack(">Q", b)[0]


# ----------------------------
# Living Cipher State
# ----------------------------


@dataclass
class LivingState:
    """
    Upgraded ratchet state:
    - Out-of-order support via skipped-key cache (bounded)
    - Periodic root ratchet via fresh X25519 DH
    - Transcript binding prevents reorder/tamper across accepted messages
    - Binary-framed headers (no delimiter parsing bugs)
    
    No ML. Deterministic. Auditable.
    """

    root_key: bytes  # 32 bytes
    chain_key_send: bytes  # 32 bytes
    chain_key_recv: bytes  # 32 bytes

    send_counter: int = 0
    recv_counter: int = 0

    # Transcript hash binds accepted message order + ciphertexts
    transcript: bytes = b"\x00" * 32

    suite: str = "H4-LIVING-AESGCM-HKDF-SHA256-v3"

    # Out-of-order receive
    ooo_window: int = 32
    skipped_keys: Dict[int, bytes] = field(
        default_factory=dict
    )  # counter -> msg_key

    # Periodic root ratchet
    root_ratchet_every: int = 1024  # M
    dh_priv: X25519PrivateKey = field(default_factory=X25519PrivateKey.generate)
    remote_dh_pub: Optional[bytes] = None

    def public_info(self) -> Dict[str, Any]:
        """Public info for introspection."""
        return {
            "suite": self.suite,
            "send_counter": self.send_counter,
            "recv_counter": self.recv_counter,
            "transcript": self.transcript.hex(),
            "ooo_window": self.ooo_window,
            "skipped_cached": len(self.skipped_keys),
            "root_ratchet_every": self.root_ratchet_every,
            "has_remote_dh": self.remote_dh_pub is not None,
        }


# ----------------------------
# Init
# ----------------------------


def init_from_shared_secret(
    shared_secret: bytes,
    context: bytes = b"Harmony\xc3\x984|LivingCipher|v3",
    *,
    ooo_window: int = 32,
    root_ratchet_every: int = 1024,
) -> LivingState:
    """Initialize from shared secret."""
    root = hkdf(shared_secret, info=context + b"|root", length=32)
    ck_s = hkdf(root, info=context + b"|ck_send", length=32)
    ck_r = hkdf(root, info=context + b"|ck_recv", length=32)
    return LivingState(
        root_key=root,
        chain_key_send=ck_s,
        chain_key_recv=ck_r,
        ooo_window=ooo_window,
        root_ratchet_every=root_ratchet_every,
    )


# ----------------------------
# Ratchets
# ----------------------------


def ratchet_step(chain_key: bytes, context: bytes, counter: int) -> Tuple[bytes, bytes]:
    """Advance chain key, derive message key."""
    next_ck = hkdf(
        chain_key, info=context + b"|ck|" + u64(counter), length=32
    )
    msg_key = hkdf(chain_key, info=context + b"|mk|" + u64(counter), length=32)
    return next_ck, msg_key


def update_transcript(
    transcript: bytes, header: bytes, ciphertext: bytes
) -> bytes:
    """Bind transcript to header + ciphertext hashes."""
    return sha256(transcript + sha256(header) + sha256(ciphertext))


def _mix_root(root_key: bytes, dh_shared: bytes, suite: str) -> bytes:
    """Mix shared secret into root key."""
    return hkdf(
        root_key + dh_shared,
        info=suite.encode("utf-8") + b"|root_mix",
        length=32,
    )


def _derive_chains_from_root(root_key: bytes, suite: str) -> Tuple[bytes, bytes]:
    """Derive send/recv chain keys from root."""
    ck_s = hkdf(root_key, info=suite.encode("utf-8") + b"|ck_send", length=32)
    ck_r = hkdf(root_key, info=suite.encode("utf-8") + b"|ck_recv", length=32)
    return ck_s, ck_r


def _should_root_ratchet(counter: int, every: int) -> bool:
    """Check if we should perform root ratchet."""
    return every > 0 and counter > 0 and (counter % every == 0)


# ----------------------------
# Header v3 (binary framed)
# ----------------------------
# Layout:
#   magic(5) = b"H4LC3"
#   suite_len(u8)
#   suite(bytes)
#   counter(u64)
#   prev_transcript(32)
#   flags(u8)
#   dh_pub(32) if flags&1 else absent
#
# flags bit0: dh_pub present

MAGIC_V3 = b"H4LC3"


def _pub_bytes(pub: X25519PublicKey) -> bytes:
    """Export X25519 public key as raw 32 bytes."""
    return pub.public_bytes(Encoding.Raw, PublicFormat.Raw)


def _build_header_v3(
    suite: str, counter: int, prev_transcript: bytes, dh_pub: Optional[bytes]
) -> bytes:
    """Build binary-framed header."""
    if len(prev_transcript) != 32:
        raise ValueError("prev_transcript must be 32 bytes")
    suite_b = suite.encode("utf-8")
    if len(suite_b) > 255:
        raise ValueError("suite too long")

    flags = 0
    extra = b""
    if dh_pub is not None:
        if len(dh_pub) != 32:
            raise ValueError("dh_pub must be 32 bytes")
        flags |= 0x01
        extra = dh_pub

    return b"".join(
        [
            MAGIC_V3,
            struct.pack(">B", len(suite_b)),
            suite_b,
            struct.pack(">Q", counter),
            prev_transcript,
            struct.pack(">B", flags),
            extra,
        ]
    )


def _parse_header_v3(header: bytes) -> Tuple[str, int, bytes, int, Optional[bytes]]:
    """Parse binary-framed header. Returns (suite, counter, prev_transcript, flags, dh_pub)."""
    if len(header) < 5 + 1 + 8 + 32 + 1:
        raise ValueError("header too short")
    if header[:5] != MAGIC_V3:
        raise ValueError("not v3 header")

    pos = 5
    suite_len = header[pos]
    pos += 1
    suite = header[pos : pos + suite_len].decode("utf-8", errors="ignore")
    pos += suite_len

    counter = struct.unpack(">Q", header[pos : pos + 8])[0]
    pos += 8

    prev_transcript = header[pos : pos + 32]
    pos += 32

    flags = header[pos]
    pos += 1

    dh_pub = None
    if flags & 0x01:
        if len(header) < pos + 32:
            raise ValueError("missing dh_pub")
        dh_pub = header[pos : pos + 32]
        pos += 32

    # ignore any trailing bytes for forward compatibility
    return suite, counter, prev_transcript, flags, dh_pub


# ----------------------------
# Out-of-order helpers
# ----------------------------


def _evict_skipped(state: LivingState) -> None:
    """Evict skipped keys outside the receive window."""
    low = max(0, state.recv_counter - state.ooo_window)
    high = state.recv_counter + state.ooo_window
    for k in list(state.skipped_keys.keys()):
        if k < low or k > high:
            del state.skipped_keys[k]


def _precompute_skipped_keys(state: LivingState, target_counter: int) -> None:
    """Precompute message keys for skipped counters WITHOUT advancing recv_counter."""
    ctx = state.suite.encode("utf-8") + b"|ratchet"
    # Derive keys from current recv_counter up to target_counter
    temp_ck = state.chain_key_recv
    for i in range(state.recv_counter, target_counter + 1):
        next_ck, mk = ratchet_step(temp_ck, ctx, i)
        state.skipped_keys[i] = mk
        temp_ck = next_ck
    _evict_skipped(state)


# ----------------------------
# Encrypt / Decrypt
# ----------------------------


def encrypt(
    state: LivingState, plaintext: bytes, aad: bytes = b""
) -> Tuple[bytes, bytes]:
    """
    Encrypt plaintext.
    
    Returns (header, ciphertext) where header is binary-framed.
    """
    dh_pub = None

    # Root ratchet: periodically refresh DH
    if _should_root_ratchet(state.send_counter, state.root_ratchet_every):
        state.dh_priv = X25519PrivateKey.generate()
        dh_pub = _pub_bytes(state.dh_priv.public_key())

        # If we have remote's DH, mix it
        if state.remote_dh_pub is not None:
            remote_pub = X25519PublicKey.from_public_bytes(state.remote_dh_pub)
            dh_shared = state.dh_priv.exchange(remote_pub)
            state.root_key = _mix_root(state.root_key, dh_shared, state.suite)
            state.chain_key_send, state.chain_key_recv = _derive_chains_from_root(
                state.root_key, state.suite
            )
            state.skipped_keys.clear()

    # Ratchet send chain
    ctx = state.suite.encode("utf-8") + b"|ratchet"
    state.chain_key_send, mk = ratchet_step(
        state.chain_key_send, ctx, state.send_counter
    )

    # Derive nonce from message key
    nonce = hkdf(mk, info=b"nonce|" + u64(state.send_counter), length=12)

    # Build header (before encryption, so we can bind it as AAD)
    header = _build_header_v3(state.suite, state.send_counter, state.transcript, dh_pub)

    # Encrypt with header as additional authenticated data
    ct = AESGCM(mk).encrypt(nonce, plaintext, aad + header)

    # Update transcript
    state.transcript = update_transcript(state.transcript, header, ct)
    state.send_counter += 1

    return header, ct


def decrypt(
    state: LivingState, header: bytes, ciphertext: bytes, aad: bytes = b""
) -> bytes:
    """
    Decrypt ciphertext.
    
    Raises on:
    - Invalid AEAD tag
    - Suite mismatch
    - Out-of-window replay
    - Transcript mismatch (tamper/reorder)
    """
    suite, counter, prev_transcript, flags, dh_pub = _parse_header_v3(header)

    if suite != state.suite:
        raise ValueError("suite mismatch")

    # If remote dh_pub present in header, mix it immediately
    if dh_pub is not None:
        state.remote_dh_pub = dh_pub
        remote_pub = X25519PublicKey.from_public_bytes(dh_pub)
        dh_shared = state.dh_priv.exchange(remote_pub)
        state.root_key = _mix_root(state.root_key, dh_shared, state.suite)
        state.chain_key_send, state.chain_key_recv = _derive_chains_from_root(
            state.root_key, state.suite
        )
        state.skipped_keys.clear()

    # Out-of-window old replay
    if counter < (state.recv_counter - state.ooo_window):
        raise ValueError("replay/out-of-window")

    # Cached out-of-order (don't commit to transcript yet)
    if counter in state.skipped_keys:
        mk = state.skipped_keys.pop(counter)
        nonce = hkdf(mk, info=b"nonce|" + u64(counter), length=12)
        pt = AESGCM(mk).decrypt(nonce, ciphertext, aad + header)
        return pt  # note: not committed to transcript until stream catches up

    # If ahead, precompute keys up to and including counter
    if counter > state.recv_counter:
        if counter - state.recv_counter > state.ooo_window:
            raise ValueError("out-of-order too far")
        # Precompute keys for counters state.recv_counter to counter
        _precompute_skipped_keys(state, counter)
        # Now counter is in skipped_keys
        mk = state.skipped_keys.pop(counter)
        nonce = hkdf(mk, info=b"nonce|" + u64(counter), length=12)
        pt = AESGCM(mk).decrypt(nonce, ciphertext, aad + header)
        _evict_skipped(state)
        return pt  # OOO, not committed to transcript

    # Now must be in-order
    if counter != state.recv_counter:
        raise ValueError("unexpected counter")

    # Check transcript matches (prevents tampering + reordering)
    if prev_transcript != state.transcript:
        raise ValueError("transcript mismatch (tamper/reorder)")

    # Ratchet recv chain
    ctx = state.suite.encode("utf-8") + b"|ratchet"
    state.chain_key_recv, mk = ratchet_step(state.chain_key_recv, ctx, state.recv_counter)

    # Derive nonce
    nonce = hkdf(mk, info=b"nonce|" + u64(state.recv_counter), length=12)

    # Decrypt with header as AAD
    pt = AESGCM(mk).decrypt(nonce, ciphertext, aad + header)

    # Update transcript
    state.transcript = update_transcript(state.transcript, header, ciphertext)
    state.recv_counter += 1
    _evict_skipped(state)

    return pt
