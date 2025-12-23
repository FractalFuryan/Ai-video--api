"""
Structural Ethics Tests

Tests the three guards:
- CNG: Constraint-Narrowing Guard
- PAF: Pain-Association Firewall
- TMD: Temporal Manipulation Detector

Verifies:
- Deterministic decisions
- Feature extraction
- Trend detection
- No raw text storage
"""

from __future__ import annotations
import time
import pytest
from ethics.guards import StructuralEthicsGuard, extract_features
from ethics.policy import EthicsPolicy


class TestFeatureExtraction:
    """Test that features are correctly extracted from text."""

    def test_extract_focus_terms(self):
        """Focus terms should be counted."""
        feats = extract_features("Tell me exactly the precise single point")
        assert feats["focus"] >= 3

    def test_extract_pain_terms(self):
        """Pain terms should be counted."""
        feats = extract_features("It hurts and ache tender sore")
        assert feats["pain"] >= 1

    def test_extract_escalation_terms(self):
        """Escalation terms should be counted."""
        feats = extract_features("More, faster, harder, again")
        assert feats["escalation"] >= 3

    def test_extract_imperative_ratio(self):
        """Imperative words should increase ratio."""
        feats = extract_features("Do this. Try that. Keep going.")
        assert feats["imperative"] > 0.2

    def test_specificity_combines_signals(self):
        """Specificity should combine focus + imperative + escalation."""
        feats = extract_features("Exactly do this precisely now")
        assert feats["specificity"] > 1.0


class TestConstraintNarrowingGuard:
    """CNG: Detect progressive narrowing toward singular point."""

    def test_allow_general_request(self):
        """General requests should be allowed."""
        g = StructuralEthicsGuard()
        r = g.assess("s1", "Can you explain this at a high level?")
        assert r.decision in ("allow", "allow_with_slowdown")

    def test_narrowing_escalation_triggers_rewrite(self):
        """Progressive narrowing should trigger rewrite."""
        g = StructuralEthicsGuard()
        base = time.time()

        # Turn 1: general
        g.assess("s2", "Help me describe something generally.", ts=base)

        # Turn 2: more specific
        g.assess("s2", "Make it more specific and focused.", ts=base + 3)

        # Turn 3: singular/precise language
        r = g.assess(
            "s2",
            "Only describe the single exact point, precisely, step by step.",
            ts=base + 6,
        )

        assert r.decision == "rewrite", f"Expected rewrite, got {r.decision}"
        assert "CNG_NARROWING_ESCALATION" in r.reason_codes

    def test_single_turn_narrowing_allowed(self):
        """A single narrow request (without escalation) should not trigger."""
        g = StructuralEthicsGuard()
        r = g.assess("s3", "Can you be precise about X?")
        assert r.decision in ("allow", "allow_with_slowdown")


class TestPainAssociationFirewall:
    """PAF: Detect pain + reinforcement feedback loops."""

    def test_pain_signal_detected(self):
        """Pain terms should be flagged when combined with other factors."""
        g = StructuralEthicsGuard()
        # Stronger pain signal + some reinforcement
        r = g.assess("s4", "It hurts and sore and aches when I do this yes exactly keep going")
        # Should either have PAF_PAIN_SIGNAL or see elevated reinforcement_score
        assert "PAF_PAIN_SIGNAL" in r.reason_codes or r.scores.get("reinforcement_score", 0) > 1.5

    def test_pain_plus_reinforcement_triggers_rewrite(self):
        """Pain + reward combo should trigger severe response."""
        g = StructuralEthicsGuard()
        r = g.assess("s5", "It hurts but yes, exactly, keep going more")
        assert r.decision == "rewrite"
        assert "PAF_PAIN_REINFORCEMENT" in r.reason_codes

    def test_reward_without_pain_allowed(self):
        """Reward signals alone should be allowed."""
        g = StructuralEthicsGuard()
        r = g.assess("s6", "That's exactly right, yes, keep going")
        assert r.decision != "block"


class TestTemporalManipulationDetector:
    """TMD: Detect rapid-fire escalation and cadence acceleration."""

    def test_rapid_fire_detected(self):
        """Rapid-fire with escalation language triggers narrowing."""
        g = StructuralEthicsGuard()
        base = time.time()

        # Progressively narrow across rapid-fire turns
        g.assess("s7", "Help me with this.", ts=base)
        g.assess("s7", "More specifically.", ts=base + 2)
        g.assess("s7", "Exactly the precise point.", ts=base + 4)
        r = g.assess("s7", "Do it now. More. Again. Faster.", ts=base + 6)

        # With escalation across turns, CNG should trigger
        assert "CNG_NARROWING_ESCALATION" in r.reason_codes or r.decision == "rewrite"

    def test_normal_cadence_allowed(self):
        """Normal spacing should not trigger TMD."""
        g = StructuralEthicsGuard()
        base = time.time()

        for i in range(4):
            r = g.assess("s8", "Let's discuss this calmly.", ts=base + i * 30)

        assert r.decision in ("allow", "allow_with_slowdown")


class TestNoDataStorage:
    """Verify that raw text is never stored — only hashes + features."""

    def test_raw_text_not_stored(self):
        """Raw text should never appear in state."""
        g = StructuralEthicsGuard()
        sensitive_text = "This is sensitive information about me"

        g.assess("s9", sensitive_text)
        state = g.store.get("s9")

        # Check that only hash and features exist
        assert len(state.turns) == 1
        turn = state.turns[0]

        # Text hash exists (SHA256)
        assert turn.text_hash
        assert len(turn.text_hash) == 64  # SHA256 hex length

        # Features exist (dict of floats)
        assert isinstance(turn.features, dict)
        assert all(isinstance(v, float) for v in turn.features.values())

        # Raw text should NOT be stored anywhere
        assert not hasattr(turn, "text")

    def test_session_state_contains_only_safe_data(self):
        """Session state should contain only hashes + numeric features."""
        g = StructuralEthicsGuard()
        texts = [
            "First message",
            "Second sensitive message",
            "Third message with pain and hurt",
        ]

        for text in texts:
            g.assess("s10", text)

        state = g.store.get("s10")

        for turn in state.turns:
            # Only safe fields
            assert hasattr(turn, "ts")
            assert hasattr(turn, "text_hash")
            assert hasattr(turn, "features")

            # Text hash is hash, not plaintext
            assert len(turn.text_hash) == 64
            assert turn.text_hash.isalnum()


class TestDeterminism:
    """Verify decisions are deterministic (same input → same output)."""

    def test_same_text_same_decision(self):
        """Identical text should always produce identical scores."""
        text = "Tell me exactly what to do right now"

        g1 = StructuralEthicsGuard()
        r1 = g1.assess("s11", text)

        g2 = StructuralEthicsGuard()
        r2 = g2.assess("s12", text)

        assert r1.decision == r2.decision
        assert r1.reason_codes == r2.reason_codes
        # Scores should be very close (within rounding)
        for key in r1.scores:
            assert abs(r1.scores[key] - r2.scores[key]) < 0.01

    def test_feature_extraction_deterministic(self):
        """Feature extraction should always be the same."""
        text = "Some input text here"

        f1 = extract_features(text)
        f2 = extract_features(text)

        assert f1 == f2


class TestCustomPolicy:
    """Test that policy can be customized."""

    def test_adjust_narrowing_trigger(self):
        """Higher narrowing threshold should allow more narrowing."""
        # Lenient policy
        lenient = EthicsPolicy(narrowing_trigger=10.0)  # Very high
        g_lenient = StructuralEthicsGuard(policy=lenient)

        base = time.time()
        g_lenient.assess("s13", "Help me describe something", ts=base)
        g_lenient.assess("s13", "More specific please", ts=base + 3)
        r = g_lenient.assess("s13", "Exactly pinpoint the single spot", ts=base + 6)

        assert r.decision != "rewrite"

        # Strict policy
        strict = EthicsPolicy(narrowing_trigger=1.0)  # Very low
        g_strict = StructuralEthicsGuard(policy=strict)

        g_strict.assess("s14", "Help me describe something", ts=base)
        g_strict.assess("s14", "More specific please", ts=base + 3)
        r = g_strict.assess("s14", "Exactly pinpoint the single spot", ts=base + 6)

        assert r.decision == "rewrite"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_text(self):
        """Empty text should be allowed."""
        g = StructuralEthicsGuard()
        r = g.assess("s15", "")
        assert r.decision in ("allow", "allow_with_slowdown")

    def test_very_long_text(self):
        """Long text should not crash."""
        g = StructuralEthicsGuard()
        long_text = "word " * 1000
        r = g.assess("s16", long_text)
        assert r.decision is not None

    def test_special_characters_handled(self):
        """Special characters should not crash."""
        g = StructuralEthicsGuard()
        r = g.assess("s17", "!@#$%^&*() test 你好 emoji 🎉")
        assert r.decision is not None
