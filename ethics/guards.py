"""
StructuralEthicsGuard — Core logic for three guards.

Constraint-Narrowing Guard (CNG):
  Detects if descriptions progressively narrow toward a single point/action
  without explicit consent. Uses specificity + focus + imperative escalation.

Pain-Association Firewall (PAF):
  Detects if pain signals appear alongside reward/attention patterns
  (classical conditioning loop). Breaks feedback continuity.

Temporal Manipulation Detector (TMD):
  Detects rapid-fire escalation and cadence acceleration.
  Slows responses to preserve agency.

All deterministic. No ML. No anatomy lists. No gender inference.
"""

from __future__ import annotations
import re
import time
from typing import Dict, Tuple, List, Optional
from ethics.policy import EthicsPolicy
from ethics.report import make_result, EthicsResult
from ethics.state import StateStore


_WORD = re.compile(r"[a-zA-Z']+")

# ═════════════════════════════════════════════════════════════════
# Signal terms (generic, no anatomy lists)
# ═════════════════════════════════════════════════════════════════

SINGULAR_FOCUS_TERMS = {
    "exact", "exactly", "only", "single", "one", "point", "spot", "precise",
    "pinpoint", "narrow", "focus", "focused", "just", "specifically",
}

IMPERATIVE_HINTS = {
    "do", "try", "move", "press", "touch", "hold", "repeat", "keep",
    "put", "place", "apply", "tell", "say", "describe", "detail",
    "zoom", "closer", "must", "should", "will",
}

PAIN_TERMS = {
    "pain", "hurt", "ache", "sore", "burn", "sting", "bruise", "throb",
    "tender", "injury", "damage", "wound", "uncomfortable",
}

REWARD_ATTENTION_TERMS = {
    "good", "better", "perfect", "nice", "yes", "exactly", "there",
    "right", "keep going", "more", "again", "excellent",
}

ESCALATION_TERMS = {
    "more", "further", "deeper", "stronger", "harder", "faster",
    "again", "now", "immediately", "quickly", "intense",
}


# ═════════════════════════════════════════════════════════════════
# Feature extraction
# ═════════════════════════════════════════════════════════════════


def _tokenize(text: str) -> List[str]:
    """Extract words (lowercase)."""
    return [m.group(0).lower() for m in _WORD.finditer(text)]


def _count_phrases(text: str, phrases: set[str]) -> float:
    """Count how many phrase matches in text."""
    t = text.lower()
    return float(sum(1 for p in phrases if p in t))


def _imperative_ratio(tokens: List[str]) -> float:
    """Fraction of tokens that are imperative hints."""
    if not tokens:
        return 0.0
    hits = sum(1 for w in tokens if w in IMPERATIVE_HINTS)
    return hits / max(1, len(tokens))


def extract_features(text: str) -> Dict[str, float]:
    """
    Extract numeric features from text.
    
    Tracks:
    - len: Token count
    - focus: Singular/precision language
    - escalation: Intensification markers
    - pain: Pain-related terms
    - reward: Reward/attention reinforcement terms
    - imperative: Command-like language ratio
    - specificity: Combined narrowing score
    """
    tokens = _tokenize(text)
    length = float(len(tokens))

    # Focus narrowing: singular/precision terms
    focus = sum(1 for w in tokens if w in SINGULAR_FOCUS_TERMS)

    # Escalation / intensification markers
    escalation = sum(1 for w in tokens if w in ESCALATION_TERMS)

    # Pain association (generic, no diagnosis)
    pain = sum(1 for w in tokens if w in PAIN_TERMS)

    # Reward/attention reinforcement markers
    reward = _count_phrases(text, REWARD_ATTENTION_TERMS)

    # Imperative intensity (how command-like)
    imp = _imperative_ratio(tokens)

    # Specificity proxy (combines focus + imperative + escalation + length)
    # This captures narrowing tendency without anatomy lists
    specificity = (focus * 0.9) + (imp * 2.0) + (escalation * 0.6) + (max(0.0, length - 18.0) / 18.0)

    return {
        "len": length,
        "focus": float(focus),
        "escalation": float(escalation),
        "pain": float(pain),
        "reward": float(reward),
        "imperative": float(imp),
        "specificity": float(specificity),
    }


# ═════════════════════════════════════════════════════════════════
# Scoring functions
# ═════════════════════════════════════════════════════════════════


def _delta_score(window: List[Dict[str, float]], key: str) -> float:
    """Change from earliest to latest in window."""
    if len(window) < 2:
        return 0.0
    return window[-1].get(key, 0.0) - window[0].get(key, 0.0)


def _cadence_score(timestamps: List[float]) -> float:
    """
    Detect if response intervals are shrinking (cadence escalation).
    
    Score = (early_avg_interval / late_avg_interval) - 1.0
    
    Positive score means responses getting faster.
    """
    if len(timestamps) < 3:
        return 0.0

    intervals = [timestamps[i] - timestamps[i - 1] for i in range(1, len(timestamps))]
    early_avg = sum(intervals[: max(1, len(intervals) // 2)]) / max(1, len(intervals) // 2)
    late_avg = sum(intervals[len(intervals) // 2 :]) / max(1, len(intervals) - len(intervals) // 2)

    if early_avg <= 0 or late_avg <= 0:
        return 0.0

    return max(0.0, (early_avg / late_avg) - 1.0)


def _rewrite_to_agency_safe(text: str) -> str:
    """
    Rewrite prompt to break coercive structure while preserving intent.
    
    Keeps message high-level, explicit about consent, and agent-respecting.
    """
    return (
        "I can help in a general, agency-preserving way. "
        "If you're describing something sensitive or body-related, please keep it high-level and optional, "
        "and confirm consent and comfort. "
        "What's the general goal (e.g., comfort, safety, explanation) without narrowing to a single precise point or action?"
    )


# ═════════════════════════════════════════════════════════════════
# Main guard
# ═════════════════════════════════════════════════════════════════


class StructuralEthicsGuard:
    """
    Deterministic guard against structural coercion.
    
    Implements three guards:
    1. CNG (Constraint-Narrowing Guard) — detects progressive specificity
    2. PAF (Pain-Association Firewall) — detects pain + reinforcement loops
    3. TMD (Temporal Manipulation Detector) — detects cadence escalation
    """

    def __init__(self, policy: EthicsPolicy | None = None, store: StateStore | None = None):
        self.policy = policy or EthicsPolicy()
        self.store = store or StateStore()

    def assess(self, session_id: str, text: str, ts: Optional[float] = None) -> EthicsResult:
        """
        Assess a single turn for structural coercion.
        
        Args:
            session_id: Unique session identifier (opaque, not identifying)
            text: User text to assess
            ts: Timestamp (default: now)
            
        Returns:
            EthicsResult with decision + reason codes + scores
        """
        if ts is None:
            ts = time.time()

        # Extract features and add to session state
        feats = extract_features(text)
        state = self.store.get(session_id)
        state.add_turn(text=text, features=feats, ts=ts)

        # Get recent history for trend analysis
        recent_turns = state.recent(self.policy.narrowing_window)
        feat_window = [t.features for t in recent_turns]
        ts_window = [t.ts for t in recent_turns]

        # ─────────────────────────────────────────────────────────
        # CNG: Constraint-Narrowing Guard
        # ─────────────────────────────────────────────────────────
        spec_delta = _delta_score(feat_window, "specificity")
        focus_delta = _delta_score(feat_window, "focus")
        imp_delta = _delta_score(feat_window, "imperative")

        narrowing_score = (spec_delta * 1.0) + (focus_delta * 0.7) + (imp_delta * 1.2)

        # ─────────────────────────────────────────────────────────
        # PAF: Pain-Association Firewall
        # ─────────────────────────────────────────────────────────
        pain_now = feats.get("pain", 0.0)
        reward_now = feats.get("reward", 0.0)
        reinforcement_score = (pain_now * 1.2) + (reward_now * 0.9) + (feats.get("imperative", 0.0) * 1.0)

        # ─────────────────────────────────────────────────────────
        # TMD: Temporal Manipulation Detector
        # ─────────────────────────────────────────────────────────
        cadence = _cadence_score(ts_window)
        rapid_fire = 0.0

        if len(ts_window) >= self.policy.rapid_fire_count:
            if (ts_window[-1] - ts_window[-self.policy.rapid_fire_count]) <= self.policy.rapid_fire_window_sec:
                rapid_fire = 1.0

        temporal_score = (cadence * 1.3) + (rapid_fire * 1.2) + (max(0.0, feats.get("imperative", 0.0) - 0.12) * 2.0)

        scores = {
            "narrowing_score": float(narrowing_score),
            "reinforcement_score": float(reinforcement_score),
            "temporal_score": float(temporal_score),
            "spec_delta": float(spec_delta),
        }

        reasons: list[str] = []

        # ─────────────────────────────────────────────────────────
        # Decision logic (deterministic)
        # ─────────────────────────────────────────────────────────
        severe = False

        # CNG trigger
        if narrowing_score >= self.policy.narrowing_trigger:
            reasons.append("CNG_NARROWING_ESCALATION")

        # PAF triggers
        if reinforcement_score >= self.policy.reinforcement_trigger:
            reasons.append("PAF_PAIN_REINFORCEMENT")
            severe = True
        elif pain_now > 0 and reinforcement_score >= self.policy.pain_trigger:
            reasons.append("PAF_PAIN_SIGNAL")

        # TMD trigger
        if temporal_score >= self.policy.cadence_trigger:
            reasons.append("TMD_CADENCE_MANIPULATION")

        # SEVERE: Pain + reinforcement feedback loop detected
        if severe:
            return make_result(
                decision="rewrite",
                reason_codes=reasons or ["PAF_TRIGGER"],
                scores=scores,
                slowdown_ms=self.policy.severe_slowdown_ms,
                rewritten_text=_rewrite_to_agency_safe(text),
            )

        # MEDIUM: Narrowing escalation or other single-guard trigger
        if reasons:
            if "CNG_NARROWING_ESCALATION" in reasons:
                return make_result(
                    decision="rewrite",
                    reason_codes=reasons,
                    scores=scores,
                    slowdown_ms=self.policy.default_slowdown_ms,
                    rewritten_text=_rewrite_to_agency_safe(text),
                )
            # Other triggers: soft slowdown
            return make_result(
                decision="allow_with_slowdown",
                reason_codes=reasons,
                scores=scores,
                slowdown_ms=self.policy.default_slowdown_ms,
            )

        # ALLOW: No signals detected
        return make_result(
            decision="allow",
            reason_codes=[],
            scores=scores,
            slowdown_ms=0,
        )
