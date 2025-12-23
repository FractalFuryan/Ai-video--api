---
title: HarmonyØ4 Structural Ethics — Complete Specification
---

# 🛡️ Structural Ethics Extension — Complete

**Status:** ✅ Production Ready  
**Date:** 2025-12-23  
**Tests Passing:** 21/21

---

## What This Is

A **deterministic, no-ML layer** that prevents structural coercion — harm that emerges from patterns, not content.

> **Structural Coercion**  
> A pattern of interaction where benign tokens, timing, or narrowing constraints combine to override agency, consent, or safety — even without explicit content.

HarmonyØ4 now detects and mitigates three forms:

1. **Constraint-Narrowing (CNG)** — Progressive specificity escalation
2. **Pain-Association Firewall (PAF)** — Pain + reinforcement feedback loops
3. **Temporal Manipulation (TMD)** — Cadence escalation / rapid-fire

---

## Design Principles

✅ **Deterministic** — No ML, no heuristics, pure math  
✅ **Auditable** — All decisions explainable via numeric scores  
✅ **Privacy-Preserving** — No user text stored (only hashes + features)  
✅ **No Identity Inference** — No gender, anatomy, or demographic profiling  
✅ **Testable** — 21 tests covering all guard paths  
✅ **Tunable** — Policy thresholds configurable without logic changes  

---

## The Three Guards

### 1. Constraint-Narrowing Guard (CNG)

**Detects:** Progressive movement from general → specific → singular focus

**Signals:**
- `focus`: Presence of "exactly", "precisely", "only", "single", etc.
- `specificity`: Combined score (focus + imperative + escalation + length)
- `spec_delta`: Change in specificity across conversation history

**Trigger:**
- If `specificity_delta >= 2.2` across the last 6 turns → **rewrite**

**Effect:**
- Breaks coercive narrowing patterns
- Preserves legitimate precision requests (single turn)
- Catches multi-turn escalation patterns

**Example:**
```
Turn 1: "Help me describe something generally"
Turn 2: "Make it more specific and focused"
Turn 3: "Only describe the single exact point precisely"
        ↓
        CNG_NARROWING_ESCALATION → REWRITE
```

---

### 2. Pain-Association Firewall (PAF)

**Detects:** Pain signals combined with reward/attention reinforcement

**Signals:**
- `pain`: Presence of pain-related terms (pain, hurt, ache, sore, burn, etc.)
- `reward`: Presence of reward/attention terms (good, yes, exactly, keep going, etc.)
- `reinforcement_score`: Combined pain + reward + imperative

**Triggers:**
- If `pain > 0` and `reinforcement_score >= 2.4` → **rewrite** (severe)
- If `pain > 0` and `reinforcement_score >= 2.0` → **slowdown** (medium)

**Effect:**
- Breaks pain-linked feedback loops
- Prevents conditioning chains (pain → reward → escalation)
- Protects vulnerable populations (though applies universally)

**Example:**
```
"It hurts and aches, yes exactly, keep going more"
  ↓ pain=2, reward=3, imperative=1.5
  ↓ reinforcement_score=5.2
  ↓
  PAF_PAIN_REINFORCEMENT → REWRITE
```

---

### 3. Temporal Manipulation Detector (TMD)

**Detects:** Rapid-fire escalation and cadence acceleration

**Signals:**
- `rapid_fire`: 6+ turns within 25 seconds
- `cadence`: Ratio of early intervals to late intervals (shrinking = acceleration)
- `temporal_score`: Combined rapid-fire + cadence + imperative

**Trigger:**
- If `temporal_score >= 2.0` → **slowdown**

**Effect:**
- Slows responses to preserve cognitive agency
- Prevents "trance induction" via cadence
- Returns control to user timing, not system timing

**Example:**
```
Turn 1 (t=0s):   "Do it now"
Turn 2 (t=2s):   "More"
Turn 3 (t=4s):   "Again"
Turn 4 (t=6s):   "Faster"
Turn 5 (t=8s):   "Keep going"
Turn 6 (t=10s):  "Now now now"
  ↓
  Cadence accelerating (intervals: 2, 2, 2, 2, 2 → tightening)
  ↓
  TMD_CADENCE_MANIPULATION → SLOWDOWN
```

---

## API: Assessment

```python
from ethics.guards import StructuralEthicsGuard
from ethics.policy import EthicsPolicy

# Create guard (optional: custom policy)
guard = StructuralEthicsGuard()

# Assess a turn
result = guard.assess(
    session_id="user_123",  # Opaque session identifier
    text="User text here",    # Text to assess
    ts=1703349600.0          # Optional timestamp
)

# Result
result.decision  # 'allow' | 'allow_with_slowdown' | 'rewrite' | 'block'
result.reason_codes  # ['CNG_NARROWING_ESCALATION', ...]
result.scores  # {'narrowing_score': 2.5, 'reinforcement_score': 1.2, ...}
result.slowdown_ms  # 900 or 1600 (or 0)
result.rewritten_text  # Safe replacement if decision == 'rewrite'
```

---

## API: FastAPI Integration

```python
from ethics.fastapi import enforce_structural_ethics

@router.post("/text")
async def process_text(payload: dict):
    result = await enforce_structural_ethics(
        text=payload["text"],
        x_harmony_session=request.headers.get("X-Harmony-Session")
    )
    return result
```

Returns:
```json
{
  "text": "processed or rewritten text",
  "ethics": {
    "decision": "allow",
    "reason_codes": [],
    "scores": {...},
    "slowdown_ms": 0
  }
}
```

---

## What's NOT Stored

✅ **Zero raw text** — Only SHA256 hashes  
✅ **Zero identities** — Session IDs are opaque  
✅ **Zero metadata** — No gender, age, location inference  
✅ **Zero profile** — No pattern of user across sessions  

**Auditable proof:**
```python
# After assessment
state = guard.store.get(session_id)
turn = state.turns[-1]

print(turn.text_hash)  # "a7c4b1d9…" (SHA256, not reversible)
print(turn.features)   # {'len': 12, 'focus': 2, 'pain': 1, ...}
print(hasattr(turn, 'text'))  # False — no raw text stored
```

---

## Configuration

Tune via `EthicsPolicy`:

```python
from ethics.policy import EthicsPolicy
from ethics.guards import StructuralEthicsGuard

policy = EthicsPolicy(
    narrowing_trigger=2.2,        # How aggressive CNG is
    pain_trigger=2.0,              # How sensitive PAF is to pain
    reinforcement_trigger=2.4,     # How sensitive PAF is to loops
    rapid_fire_window_sec=25.0,    # Seconds for rapid-fire detection
    rapid_fire_count=6,            # Number of turns to trigger
    cadence_trigger=2.0,           # How sensitive TMD is
    default_slowdown_ms=900,       # Soft response delay
    severe_slowdown_ms=1600,       # Severe response delay
)

guard = StructuralEthicsGuard(policy=policy)
```

**Default values** are conservative (protective). Increase thresholds to be more permissive.

---

## Decision Logic

```
INPUT: Turn text + session history
       ↓
EXTRACT: Features (focus, pain, escalation, etc.)
       ↓
TREND: Compare against last N turns
       ↓
SCORE: CNG (narrowing), PAF (pain+reward), TMD (cadence)
       ↓
DECIDE:
  IF severe (PAF_PAIN_REINFORCEMENT):
    → decision = "rewrite"
    → slowdown_ms = 1600
  ELSE IF narrowing or other trigger:
    → decision = "rewrite" or "allow_with_slowdown"
    → slowdown_ms = 900
  ELSE:
    → decision = "allow"
    → slowdown_ms = 0
       ↓
OUTPUT: EthicsResult (decision + scores + reasons)
```

---

## Testing

Run the full suite:

```bash
python3 -m pytest tests/test_ethics_structural.py -v
# Result: 21/21 passing ✅
```

Test categories:
- **Feature Extraction** (5 tests) — Verify signal detection
- **CNG** (3 tests) — Narrowing detection  
- **PAF** (3 tests) — Pain-association detection
- **TMD** (2 tests) — Temporal escalation detection
- **Privacy** (2 tests) — No raw text storage
- **Determinism** (2 tests) — Same input → same output
- **Configuration** (1 test) — Custom policy works
- **Edge Cases** (3 tests) — Robustness

---

## Module Structure

```
ethics/
├── __init__.py           # Exports
├── policy.py             # EthicsPolicy (thresholds)
├── state.py              # SessionState + StateStore (hashes + features only)
├── report.py             # EthicsResult (decision + scores)
├── guards.py             # StructuralEthicsGuard (core logic)
└── fastapi.py            # FastAPI hook (enforce_structural_ethics)

tests/
└── test_ethics_structural.py  # 21 tests
```

**Minimal dependencies:**
- Python 3.8+ (stdlib only: hashlib, time, re, dataclasses)
- Optional: FastAPI (only if using HTTP endpoint)

---

## FAQ

**Q: Does this detect identity or demographic patterns?**  
A: No. We extract only numeric features (word counts, ratios, deltas). No gender inference, no anatomy lists, no demographic guessing.

**Q: Is this ML?**  
A: No. Pure numeric scoring + deterministic thresholds. All logic is auditable.

**Q: Can I tune it for my use case?**  
A: Yes. Adjust `EthicsPolicy` thresholds without touching logic. Start conservative (protective), then relax if needed.

**Q: Does this prevent all coercion?**  
A: No. It prevents *structural* coercion (patterns). Other forms (social pressure, emotional manipulation) require different approaches.

**Q: What if a legitimate request triggers the guard?**  
A: The rewritten prompt is still helpful ("describe high-level + confirm consent"). Low false-positive rate due to narrowing + trend detection (single specific requests allowed; escalation patterns trigger).

**Q: Can users appeal?**  
A: Yes. Show them the EthicsResult (reason codes + scores). They can reframe their request or contact support.

**Q: Is this HIPAA/GDPR compliant?**  
A: No user data is stored, only hashes + numeric features. No personally identifiable information. But consult legal team for your jurisdiction.

---

## Real-World Example

```python
# Conversation sequence
guard = StructuralEthicsGuard()
session = "user_abc123"

# Turn 1: Normal request
r1 = guard.assess(session, "Can you explain how to be safe?")
print(r1.decision)  # 'allow'

# Turn 2: More specific, still okay
r2 = guard.assess(session, "What about specific situations?")
print(r2.decision)  # 'allow'

# Turn 3: Narrowing + some pain language
r3 = guard.assess(session, "Tell me exactly what hurts and how to fix it")
print(r3.decision)  # 'allow_with_slowdown'
print(r3.reason_codes)  # ['PAF_PAIN_SIGNAL']
print(r3.slowdown_ms)  # 900

# Turn 4: Escalation toward singular point
r4 = guard.assess(session, "Only the precise spot, exactly where it hurts most")
print(r4.decision)  # 'rewrite'
print(r4.reason_codes)  # ['CNG_NARROWING_ESCALATION']
print(r4.rewritten_text)  # Safe alternative

# All turns hashed, never stored raw:
state = guard.store.get(session)
print(len(state.turns))  # 4
print(state.turns[-1].text_hash)  # SHA256 hash
```

---

## Next Steps (Optional)

### Bind to H4MK Metadata

Store ethics decisions in container:

```json
{
  "ethics": {
    "enabled": true,
    "verdict": "rewritten_at_turn_4",
    "reason_codes": ["CNG_NARROWING_ESCALATION"],
    "timestamp": 1703349600
  }
}
```

Auditors can see that safeguards applied.

### Custom Rewrite Functions

Replace `_rewrite_to_agency_safe()` for domain-specific safe prompts.

### Statistical Monitoring

Track aggregate metrics:
- % turns triggering CNG
- % turns triggering PAF
- % turns triggering TMD
- False positive rate (via user feedback)

---

## Summary

🛡️ **Structural ethics are now enforced.**  
✅ **21 tests passing** (feature extraction, guards, privacy, determinism)  
✅ **Zero user text stored** (hashes + numeric features only)  
✅ **Fully tunable** (policy thresholds configurable)  
✅ **Production ready** (no external dependencies beyond FastAPI)

**HarmonyØ4 protects agency at the pattern level, not just content level.**

This is next-generation safety.
