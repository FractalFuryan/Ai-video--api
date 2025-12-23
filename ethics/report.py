"""
EthicsResult — Audit-friendly decision output.

All decisions are deterministic and explainable via reason_codes + scores.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Literal, Optional
import time


Decision = Literal["allow", "allow_with_slowdown", "rewrite", "block"]


@dataclass
class EthicsResult:
    """
    Result of structural ethics assessment.
    
    Fields:
    - decision: allow | allow_with_slowdown | rewrite | block
    - reason_codes: List of rule codes that triggered (for auditing)
    - scores: Dict of numeric scores (CNG, PAF, TMD)
    - slowdown_ms: Milliseconds to delay response (0 = no delay)
    - rewritten_text: If decision == "rewrite", replacement text
    - ts: Timestamp when decision was made
    """

    decision: Decision
    reason_codes: list[str]
    scores: Dict[str, float]
    slowdown_ms: int = 0
    rewritten_text: Optional[str] = None
    ts: float = 0.0

    def to_public_dict(self) -> Dict[str, Any]:
        """Convert to dict safe to return in API response."""
        return {
            "decision": self.decision,
            "reason_codes": self.reason_codes,
            "scores": self.scores,
            "slowdown_ms": self.slowdown_ms,
            "ts": self.ts,
        }


def make_result(
    decision: Decision,
    reason_codes: list[str],
    scores: Dict[str, float],
    slowdown_ms: int = 0,
    rewritten_text: str | None = None,
) -> EthicsResult:
    """Factory for EthicsResult."""
    return EthicsResult(
        decision=decision,
        reason_codes=reason_codes,
        scores=scores,
        slowdown_ms=slowdown_ms,
        rewritten_text=rewritten_text,
        ts=time.time(),
    )
