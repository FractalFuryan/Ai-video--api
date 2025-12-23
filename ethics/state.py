"""
SessionState — Minimal, privacy-preserving session tracking.

Stores only:
- Text hashes (SHA256, not reversible)
- Numeric feature vectors (length, focus, escalation, etc.)
- Timestamps

NO raw user text. NO identity data. NO logs of sensitive content.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import hashlib
import time


def _sha256_hex(s: str) -> str:
    """Compute SHA256 of string. Not reversible."""
    return hashlib.sha256(s.encode("utf-8", errors="ignore")).hexdigest()


@dataclass
class Turn:
    """Single turn: hash + features + timestamp. Never stores raw text."""

    ts: float  # Unix timestamp
    text_hash: str  # SHA256 hash (not reversible, not identifying)
    features: Dict[str, float]  # Numeric features only (length, focus, pain, etc.)


@dataclass
class SessionState:
    """Conversation state for a single session."""

    session_id: str
    turns: List[Turn] = field(default_factory=list)

    def add_turn(self, text: str, features: Dict[str, float], ts: Optional[float] = None) -> None:
        """Add a turn. Only stores hash + features, never raw text."""
        if ts is None:
            ts = time.time()
        self.turns.append(Turn(ts=ts, text_hash=_sha256_hex(text), features=features))

    def recent(self, n: int) -> List[Turn]:
        """Get last n turns."""
        return self.turns[-n:]


class StateStore:
    """
    In-memory session storage.
    Can be swapped for Redis/Postgres/etc later without changing API.
    """

    def __init__(self):
        self._sessions: Dict[str, SessionState] = {}

    def get(self, session_id: str) -> SessionState:
        """Get or create session state."""
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionState(session_id=session_id)
        return self._sessions[session_id]

    def delete(self, session_id: str) -> None:
        """Delete session (for privacy cleanup)."""
        if session_id in self._sessions:
            del self._sessions[session_id]

    def clear_all(self) -> None:
        """Clear all sessions (for testing)."""
        self._sessions.clear()
