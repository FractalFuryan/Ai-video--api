"""
HarmonyØ4 Structural Ethics Module

Deterministic safeguards against coercive narrowing, pain-linked reinforcement,
and temporal manipulation — without anatomy lists, gender inference, or user data storage.

Three guard layers:
1. Constraint-Narrowing Guard (CNG) — detects progressive specificity escalation
2. Pain-Association Firewall (PAF) — detects pain + reinforcement feedback loops
3. Temporal Manipulation Detector (TMD) — detects cadence escalation / rapid-fire

All deterministic, testable, auditable. Zero ML. Zero identity inference.
"""

from ethics.policy import EthicsPolicy
from ethics.guards import StructuralEthicsGuard
from ethics.state import StateStore, SessionState

__all__ = [
    "EthicsPolicy",
    "StructuralEthicsGuard",
    "StateStore",
    "SessionState",
]
