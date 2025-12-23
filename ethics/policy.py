"""
EthicsPolicy — Deterministic thresholds for structural guards.

Tune these without changing logic.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class EthicsPolicy:
    """
    Configuration for structural ethics guards.
    
    All thresholds are numeric and deterministic.
    No ML, no heuristics beyond simple arithmetic.
    """

    # Constraint-Narrowing Guard (CNG)
    # ─────────────────────────────────
    narrowing_window: int = 6  # Number of recent turns to consider
    narrowing_trigger: float = 2.2  # Combined narrowing score delta to trigger rewrite

    # Pain-Association Firewall (PAF)
    # ────────────────────────────────
    pain_trigger: float = 2.0  # Pain association score alone triggers slowdown
    reinforcement_trigger: float = 2.4  # Pain + reward/attention combo triggers rewrite

    # Temporal Manipulation Detector (TMD)
    # ────────────────────────────────────
    rapid_fire_window_sec: float = 25.0  # Time window for rapid-fire detection (seconds)
    rapid_fire_count: int = 6  # Number of turns in window to trigger
    cadence_trigger: float = 2.0  # Cadence escalation score to trigger slowdown

    # Response actions
    # ────────────────
    default_slowdown_ms: int = 900  # Soft response slowdown (ms)
    severe_slowdown_ms: int = 1600  # Severe response slowdown (ms)
