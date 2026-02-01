# 🔷 HarmonyØ4 Ethical Geometry Generator — Phases G0-G5

## 🎯 **VISION: Category Exit**

We're not building another image generator with ethics bolted on. We're building **sealed spatial programs** — geometry-based generation that's fundamentally impossible to misuse for deepfakes.

**The Core Insight:** Pixels are dangerous. Geometry is safe.

---

## 📊 **SYSTEM ARCHITECTURE**

```
User Prompt (Natural Language)
         ↓
    [PHASE G1: Deterministic Parser]
    (Rule-based, NO ML, NO randomness)
         ↓
   Geometry Tokens (Structure Only)
         ↓
    [PHASE G2: Ethics Guard]
    (Hard filters: No faces, no biometrics, no identity)
         ↓
   Validated Tokens
         ↓
    [PHASE G3: Temporal Generator]  +  [PHASE G4: Container Integration]
    (Time-based transforms)           (H4MK sealing)
         ↓
   Sealed Geometry Sequence
         ↓
    [PHASE G5: WebGL Viewer]
    (Client-side rendering, never pixels)
         ↓
   Real-time 3D Geometry Visualization
```

---

## 🏗️ **PHASES IMPLEMENTED**

### **PHASE G0: Formal Geometry Language** ✅
**File:** `geometry/spec.py`

- **Immutable tokens** — frozen dataclasses, deterministic UIDs
- **Structure-only representation** — no pixels, mesh, or texture data
- **Canonical geometry kinds** — cube, sphere, cylinder, cone, torus, plane
- **Numeric parameters only** — no string-based identity markers
- **Version 1 specification** — immutable schema for auditing

**Key Classes:**
```python
GeometryToken(frozen=True, eq=True)  # Immutable
  - token_type: GeometryTokenType
  - kind: str
  - params: Dict[str, float]  # Numeric only
  - bounds: Tuple[float, float, float]
  - uid: str  # Deterministic, content-addressed
```

**Example:**
```python
from geometry.spec import create_primitive
cube = create_primitive("cube", size=2.0)
# ✓ Token UID: g04cd1463828ada00 (deterministic)
# ✓ Parameters: {"size": 2.0}
# ✓ Immutable: cube.kind = "sphere"  → FrozenInstanceError
```

---

### **PHASE G1: Deterministic Prompt → Geometry** ✅
**File:** `generators/transformers/prompt_to_geometry.py`

- **Rule-based parsing** — fixed regex patterns, no embeddings
- **Deterministic** — same prompt always produces same tokens
- **Stop words** — explicit rejection of anatomy/identity language
- **Pattern extension** — carefully curated geometry mappings

**Example:**
```python
from generators.transformers.prompt_to_geometry import parse_prompt

tokens = parse_prompt("large rotating cube")
# ✓ Returns: [PrimitiveToken(cube), TransformToken(scale), TransformToken(rotate_y)]
# ✓ Deterministic UID — reproducible across systems
# ✗ parse_prompt("human face")  → ValueError: "disallowed content"
```

**Supported Patterns:**
- Primitives: cube, sphere, cylinder, cone, torus, plane
- Modifiers: large, small, wide, tall
- Transforms: rotate, tilt, move

---

### **PHASE G2: Ethical Structural Filter** ✅
**File:** `ethics/constraints.py`

**GeometryEthicsGuard — Hard Filter, Non-Negotiable**

```python
from ethics.constraints import safe_validate_geometry, validate_geometry

# Safe validation (returns report)
report = safe_validate_geometry(tokens)
assert report["valid"]  # True for pure geometry

# Strict validation (raises if invalid)
validate_geometry(tokens)  # ✓ Passes for allowed geometry
# ✗ Raises ValueError if forbidden patterns detected
```

**Three-Layer Defense:**

1. **Forbidden Kinds** — Explicit blocklist
   - Anatomy: face, head, eye, nose, mouth, ear, hand, body
   - Biometric proxies: oval, silhouette, profile, mask
   - Identity markers: portrait, bust, statue

2. **Forbidden Parameters** — Biometric measurement names
   - ratio, proportion, spacing, distance
   - symmetry, asymmetry

3. **Biometric Pattern Detection** — Face-like proportions
   - Detects dimensional ratios matching facial geometry
   - Golden ratio recognition (0.6-0.62 eye spacing range)

**Validation Report:**
```python
{
    "valid": True,
    "violations": [],
    "token_count": 2,
    "token_types": ["primitive", "transform"],
    "kinds": ["cube", "rotate_y"],
    "checks_performed": [
        "forbidden_kinds",
        "forbidden_params", 
        "biometric_patterns"
    ]
}
```

---

### **PHASE G3: Temporal Geometry System** ✅
**File:** `geometry/temporal.py`

**Video without video** — Time-based transformations as geometry tokens, not pixel sequences.

```python
from geometry.temporal import TemporalGeometryGenerator, TemporalSequence

generator = TemporalGeometryGenerator(fps=30)
sequences = generator.create_animation([cube], duration_seconds=5.0)

# ✓ Returns TemporalSequence objects, NOT pixel video
# ✓ Keyframe-based interpolation (linear, ease_in_out, bounce, spring)
# ✓ Each sequence references a token by UID
```

**Temporal Features:**
- **Keyframe system** — frame-accurate temporal data
- **Interpolation methods** — LINEAR, EASE_IN_OUT, BOUNCE, SPRING, STEP
- **Animation export** — Complete temporal data as JSON/CBOR
- **Efficient encoding** — Sequences reference token UIDs, not duplicated geometry

**Example Sequence:**
```python
TemporalSequence(
    target_uid="g04cd1463828ada00",  # References cube token
    property_name="rotate_y.angle",
    keyframes=[
        TemporalKeyframe(frame=0, value=0),
        TemporalKeyframe(frame=150, value=360),  # Full rotation
    ],
    duration_frames=150  # 5 seconds at 30fps
)
```

---

### **PHASE G4: HarmonyØ4 Container Integration** ✅
**File:** `container/geometry_container.py`

**Sealed, Auditable Geometry Storage**

```python
from container.geometry_container import create_geometry_container

# Create geometry container from H4MK
geom_container = create_geometry_container(h4mk_container)

# Store geometry and temporal data
geom_hash = geom_container.add_geometry_tokens(tokens)
temp_hash = geom_container.add_temporal_sequences(sequences)

# Retrieve with full integrity validation
tokens = geom_container.get_geometry_tokens()
report = geom_container.create_geometry_summary()
```

**Chunk Types:**
- `GEOM` — Geometry token data (JSON)
- `TEMP` — Temporal sequences (JSON)
- `GMET` — Geometry metadata (JSON)

**Container Features:**
- Deterministic hashing — Same geometry = Same hash
- Integrity validation — Checksums verified on load
- Metadata tracking — Token counts, types, bounds
- Export formats — JSON, CBOR (extensible to glTF, USD)

**Geometry Summary:**
```python
{
    "geometry": {
        "token_count": 2,
        "primitive_count": 1,
        "transform_count": 1,
        "temporal_count": 0
    },
    "animation": {
        "sequence_count": 2,
        "duration_frames": 150,
        "animated_properties": ["rotate_y.angle", "uniform_scale.factor"]
    },
    "bounds": {
        "min_x": -1.0, "max_x": 1.0,
        "min_y": -1.0, "max_y": 1.0,
        "min_z": -1.0, "max_z": 1.0
    },
    "integrity_check": True
}
```

---

### **PHASE G5: Geometry Viewer & API** ✅
**File:** `api/routes/geometry.py`

**Endpoints:**

1. **POST `/geometry/generate`** — Generate from prompt
   ```bash
   curl -X POST http://localhost:8000/geometry/generate \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "large spinning cube",
       "duration_seconds": 5.0,
       "fps": 30
     }'
   ```
   Response:
   ```json
   {
     "tokens": [
       {"token_type": "primitive", "kind": "cube", "params": {...}},
       {"token_type": "transform", "kind": "scale", "params": {...}}
     ],
     "validation_report": {"valid": true, ...},
     "temporal": {...},
     "summary": {...}
   }
   ```

2. **GET `/geometry/viewer/{data_hash}`** — Interactive WebGL viewer
   - Real-time 3D visualization
   - Orbit controls, wireframe toggle, timeline scrubbing
   - Client-side rendering (no server-side image generation)

3. **GET `/geometry/primitives`** — List available geometry
   ```json
   {
     "primitives": ["cube", "sphere", "cylinder", "cone", "torus", "plane"],
     "transforms": ["translate", "rotate_x", "rotate_y", "rotate_z", "scale"],
     "description": "Canonical geometry tokens for ethical generation"
   }
   ```

4. **POST `/geometry/test-parse`** — Debug prompt parsing
   ```bash
   curl "http://localhost:8000/geometry/test-parse?prompt=cube%20and%20sphere"
   ```

5. **GET `/geometry/health`** — System status
   ```json
   {
     "status": "ok",
     "system": "HarmonyØ4 Geometry Generator (G0-G5)",
     "capabilities": [
       "deterministic_prompt_parsing",
       "ethical_validation",
       "temporal_animation",
       "container_integration",
       "webgl_viewing"
     ]
   }
   ```

---

## 🧪 **TESTING & VALIDATION**

### **Run Foundation Tests**
```bash
# Test all phases
python -c "
from geometry.spec import create_primitive
from generators.transformers.prompt_to_geometry import parse_prompt
from ethics.constraints import safe_validate_geometry
from geometry.temporal import TemporalGeometryGenerator

# Test 1: Geometry creation
cube = create_primitive('cube', size=2.0)
assert cube.uid.startswith('g')

# Test 2: Prompt parsing
tokens = parse_prompt('large rotating cube')
assert len(tokens) >= 2

# Test 3: Ethics validation
report = safe_validate_geometry(tokens)
assert report['valid']

# Test 4: Temporal animation
gen = TemporalGeometryGenerator(fps=30)
sequences = gen.create_animation([cube], duration_seconds=2.0)
assert sequences[0].duration_frames == 60

print('✅ All tests passed!')
"
```

### **Test Prompt Rejection**
```bash
# This should be rejected
curl "http://localhost:8000/geometry/test-parse?prompt=human%20face"
# Response: {"status": "rejected", "error": "Prompt contains disallowed content..."}
```

---

## 📁 **FILE STRUCTURE**

```
harmonyø4/
├── geometry/                          # Core geometry library
│   ├── __init__.py
│   ├── spec.py                        # G0: Token specification
│   ├── temporal.py                    # G3: Temporal sequences
│   ├── tokens/
│   │   ├── __init__.py
│   │   └── base.py                    # (spec.py replaces this)
│   ├── operations/
│   └── compositions/
│
├── generators/                        # Generation pipeline
│   ├── __init__.py
│   ├── transformers/
│   │   ├── __init__.py
│   │   └── prompt_to_geometry.py      # G1: Prompt parsing
│   ├── constraints/
│   └── renderers/
│
├── ethics/                            # Ethical constraints
│   ├── __init__.py
│   └── constraints.py                 # G2: Ethics guard
│
├── container/                         # H4MK integration
│   ├── __init__.py
│   ├── geometry_container.py          # G4: Container storage
│   └── h4mk.py                        # (existing)
│
├── api/routes/
│   ├── geometry.py                    # G5: API endpoints
│   └── generation/                    # (optional generation routes)
│
└── api/main.py                        # (updated with geometry router)
```

---

## 🚀 **DEPLOYMENT CHECKLIST**

✅ **G0: Geometry Specification**
- [x] Immutable token definitions
- [x] Deterministic UID generation
- [x] Canonical geometry kinds
- [x] Serialization (to_dict, from_dict)

✅ **G1: Prompt Parsing**
- [x] Rule-based pattern matching
- [x] Stop-word rejection
- [x] Modifier application
- [x] Deterministic output

✅ **G2: Ethics Guard**
- [x] Forbidden kinds list
- [x] Parameter name validation
- [x] Biometric pattern detection
- [x] Validation reporting

✅ **G3: Temporal System**
- [x] Keyframe interpolation
- [x] Animation generation
- [x] Temporal token creation
- [x] Export functionality

✅ **G4: Container Integration**
- [x] Chunk-based storage
- [x] Integrity validation
- [x] Metadata tracking
- [x] Summary generation

✅ **G5: Viewer & API**
- [x] Generation endpoint
- [x] WebGL viewer (HTML5/Three.js)
- [x] Primitive listing
- [x] Health check endpoint

---

## 🔐 **Security & Ethics Properties**

### **Anti-Deepfake Guarantees:**
1. ✅ **No pixel generation** — Only geometry tokens
2. ✅ **No facial geometry** — Hard-coded blocklist
3. ✅ **No identity parameters** — No ratios, no spacing values
4. ✅ **No biometric proxies** — No silhouettes, profiles, or symmetry
5. ✅ **Sealed & auditable** — All geometry sealed in H4MK containers
6. ✅ **Deterministic** — Same input = Same output always

### **Audit Trail:**
- Geometry tokens include version and UID
- Temporal sequences reference tokens by UID (traceability)
- Container metadata tracks generation lineage
- All data JSON-serializable for forensics

---

## 📈 **NEXT STEPS**

### **Phase G6: Advanced Geometry (Planned)**
- Composite shapes (hierarchies)
- Constraint-based generation (symmetry, alignment)
- Physics-based simulation (collision detection)

### **Phase G7: Rendering Pipeline (Planned)**
- Server-side geometry-to-glTF export
- Real-time WebGL rendering optimization
- Progressive streaming for large models

### **Phase G8: Federated Geometry Library (Planned)**
- Community-contributed shapes
- Cryptographic validation of user-submitted geometry
- Trustless geometry exchange network

---

## 📚 **Documentation**

- **API Docs**: `GET /docs` → Swagger UI
- **Specification**: This file + inline docstrings
- **Examples**: See test commands above

---

## ✨ **Why This Matters**

This is **not just** an ethics add-on. It's a **fundamental architecture decision** to make video/image generation **structurally incapable** of producing deepfakes.

By tokenizing structure instead of pixels, and sealing in HarmonyØ4 containers, we've created a system where:
- You cannot sneak identity data past the guards
- You cannot mix geometry with pixel-based renderings
- Every generated artifact is cryptographically auditable
- The format itself prevents misuse

**This is category exit.** We're not in the image generation race. We're in the *ethical spatial computing* race.

---

**Deployed:** February 1, 2026  
**Status:** ✅ Production Ready  
**Next Update:** When Phase G6 completes  
