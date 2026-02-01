# 🔷 HarmonyØ4 Geometry Generator — Quick Start

## 🚀 **Fast API Integration**

Already wired into `api/main.py`:
```python
from api.routes.geometry import router as geometry_router
app.include_router(geometry_router)  # All endpoints under /geometry
```

---

## 📝 **5-Minute Examples**

### **1. Generate Geometry from Prompt**
```bash
curl -X POST http://localhost:8000/geometry/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "large rotating cube and small sphere",
    "duration_seconds": 5.0,
    "fps": 30
  }'
```

**Response:** Geometry tokens + validation + temporal sequences

### **2. List Available Shapes**
```bash
curl http://localhost:8000/geometry/primitives
```

### **3. View in WebGL**
```bash
# After generation, access viewer at:
open http://localhost:8000/geometry/viewer/{data_hash}
```

### **4. Test Prompt Parsing**
```bash
curl "http://localhost:8000/geometry/test-parse?prompt=cube%20and%20sphere"
```

### **5. Health Check**
```bash
curl http://localhost:8000/geometry/health
```

---

## 🛡️ **Ethics Guarantees**

**Automatically Rejected:**
```bash
curl "http://localhost:8000/geometry/test-parse?prompt=human%20face"
# → {"status": "rejected", "error": "Prompt contains disallowed content..."}
```

**Allowed Geometry:**
- Primitives: cube, sphere, cylinder, cone, torus, plane
- Transforms: rotate, translate, scale
- Temporal: keyframe animations

**Forbidden Content:**
- Anatomical terms (face, head, eye, hand, body, etc.)
- Identity markers (portrait, bust, character, etc.)
- Biometric proxies (silhouette, profile, symmetry, etc.)

---

## 🔧 **Python Usage**

### **Generate Geometry**
```python
from geometry.spec import create_primitive
from generators.transformers.prompt_to_geometry import parse_prompt
from ethics.constraints import safe_validate_geometry

# Create directly
cube = create_primitive("cube", size=2.0)

# Or parse from prompt
tokens = parse_prompt("large rotating cube")

# Validate
report = safe_validate_geometry(tokens)
assert report["valid"]
```

### **Generate Temporal Sequences**
```python
from geometry.temporal import TemporalGeometryGenerator

generator = TemporalGeometryGenerator(fps=30)
sequences = generator.create_animation([cube], duration_seconds=5.0)

# Access keyframes
for seq in sequences:
    for kf in seq.keyframes:
        print(f"Frame {kf.frame}: {kf.value}")
```

### **Container Integration**
```python
from container.geometry_container import create_geometry_container

# Store in H4MK
geom_container = create_geometry_container(h4mk_container)
geom_hash = geom_container.add_geometry_tokens(tokens)
temp_hash = geom_container.add_temporal_sequences(sequences)

# Retrieve & validate
tokens = geom_container.get_geometry_tokens()
summary = geom_container.create_geometry_summary()
print(summary)
```

---

## 📊 **Token Structure**

### **Geometry Token**
```python
{
    "token_type": "primitive",      # primitive, transform, temporal, relation, composition
    "kind": "cube",                 # cube, sphere, cylinder, cone, torus, plane
    "params": {"size": 2.0},        # Numeric parameters only
    "bounds": [2.0, 2.0, 2.0],     # x, y, z extents
    "uid": "g04cd1463828ada00",     # Deterministic content-addressed UID
    "version": 1
}
```

### **Temporal Sequence**
```python
{
    "target_uid": "g04cd1463828ada00",    # References token UID
    "property_name": "rotate_y.angle",    # What property to animate
    "keyframes": [                        # Temporal keypoints
        {"frame": 0, "value": 0.0, "interpolation": "linear"},
        {"frame": 150, "value": 360.0, "interpolation": "linear"}
    ],
    "duration_frames": 150               # Total duration
}
```

---

## ✅ **Validation Report**

Every generated geometry includes:
```python
{
    "valid": True,
    "violations": [],
    "token_count": 2,
    "token_types": ["primitive", "transform"],
    "kinds": ["cube", "rotate_y"],
    "strict_mode": True,
    "checks_performed": [
        "forbidden_kinds",
        "forbidden_params",
        "biometric_patterns"
    ]
}
```

---

## 🎯 **Key Design Principles**

1. **No Pixels** — Only geometry tokens
2. **No Identity** — Explicit blocklist of anatomy/biometric terms
3. **Deterministic** — Same input = Same output always
4. **Sealed** — All data cryptographically sealed in H4MK containers
5. **Auditable** — Full lineage tracking via UIDs and metadata

---

## 📖 **Full Documentation**

See `GEOMETRY_IMPLEMENTATION.md` for complete specification, architecture, and deployment details.

---

**Status:** ✅ Production Ready  
**Endpoints:** 5 active (generate, viewer, primitives, test-parse, health)  
**Phases:** G0-G5 complete (G0 spec → G5 viewer)
