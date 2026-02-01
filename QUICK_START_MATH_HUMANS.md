# 🚀 QUICK START: Deploy in 2 Minutes

## One-Command Deployment

```bash
cd /workspaces/Ai-video--api
./scripts/deploy_math_humans.sh
```

That's it! The script will:
✅ Generate cryptographic secrets  
✅ Build Docker containers  
✅ Start all services  
✅ Run verification tests  
✅ Confirm everything works  

**Time**: ~2 minutes  
**Result**: Full working system  

---

## Test Immediately After Deployment

### 1. Generate a Face

```bash
curl -X POST http://localhost:8000/math-humans/generate \
  -H "Content-Type: application/json" \
  -d '{"method":"golden_ratio","style":"classical"}'
```

Look for: `container_hash` in response

### 2. Copy Hash and Verify

```bash
# Replace HASH with the container_hash from step 1
curl http://localhost:8000/math-humans/HASH/verify | python -m json.tool
```

Look for: All harm prevention guarantees verified ✅

### 3. Check Status

```bash
curl http://localhost:8000/math-humans/system-status | python -m json.tool
```

Look for: All modules `status: "operational"`

---

## 5 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/math-humans/generate` | POST | Create mathematical human |
| `/math-humans/{hash}/verify` | GET | Verify ethical guarantees |
| `/math-humans/construction-methods` | GET | List 6 mathematical methods |
| `/math-humans/philosophy` | GET | View system principles |
| `/math-humans/system-status` | GET | Full system health |

---

## What You Can Generate

### 6 Mathematical Methods

```
1. Golden Ratio       (Fibonacci beauty)
2. Fractal Features   (Self-similar patterns)
3. Topological Morph  (Smooth deformations)
4. Symmetry Groups    (Group theory elegance)
5. Harmonic Composition (Fourier series)
6. Fibonacci Growth   (Natural spirals)
```

### 5 Artistic Styles

```
1. Classical          (Greek/Roman ideals)
2. Renaissance        (Humanist principles)
3. Modern Abstract    (Geometric forms)
4. Stylized          (Artistic exaggeration)
5. Minimalist        (Essential features)
```

### 3 Safety Levels

```
1. Strict (default)   (Maximum safety)
2. Artistic          (Creative freedom)
3. Academic          (Anatomical accuracy)
```

---

## Generation Examples

### Simple (Minimal Parameters)

```bash
curl -X POST http://localhost:8000/math-humans/generate \
  -H "Content-Type: application/json" \
  -d '{"method":"golden_ratio"}'
```

### Complete (All Options)

```bash
curl -X POST http://localhost:8000/math-humans/generate \
  -H "Content-Type: application/json" \
  -d '{
    "seed": 42,
    "method": "golden_ratio",
    "style": "classical",
    "safety_level": "strict",
    "detail_level": 0.7,
    "geometric_influence": 0.8,
    "stylization": 0.5,
    "context": "portrait study",
    "include_proofs": true
  }'
```

---

## Response Structure

```json
{
  "human_id": "math_human_abc123",
  "container_hash": "abc123def456...",
  
  "harm_prevention": {
    "deepfake_prevention": true,
    "exploitation_prevention": true,
    "bias_prevention": true,
    "violence_prevention": true,
    "deception_prevention": true,
    "verified": true
  },
  
  "mathematical_proofs": {
    "no_training_data": true,
    "non_injective": true,
    "deterministic": "seed_42"
  },
  
  "public_verification_url": "/math-humans/abc123def456/verify"
}
```

---

## Safety Guarantees

| Harm | Prevention | How |
|------|-----------|-----|
| Deepfakes | 1024 equivalence classes | Many-to-one, can't reverse |
| Exploitation | Classical proportions | No photorealistic biometrics |
| Bias | Universal beauty (φ) | No racial parameters |
| Violence | Restricted parameters | No weapons/gore |
| Deception | Cryptographic sealing | Clearly labeled + verifiable |

---

## Troubleshooting

### Services won't start
```bash
docker ps                                      # Check Docker
docker-compose logs harmony4-api               # View logs
```

### Generation returns error
- Check JSON syntax
- Verify method is valid (see 6 methods above)
- Verify style is valid (see 5 styles above)
- Verify safety_level is valid (see 3 levels above)

### Verification fails
- Verify hash is correct
- Check generation succeeded first
- Check Docker logs

### Need help?
1. Read: [PRODUCTION_DEPLOYMENT_GUIDE.md](PRODUCTION_DEPLOYMENT_GUIDE.md)
2. Check: `curl http://localhost:8000/math-humans/system-status`
3. Logs: `docker-compose -f docker-compose.geometry.yml logs`

---

## Next Steps

### Option 1: Just Deploy

```bash
./scripts/deploy_math_humans.sh
# Done! System is running
```

### Option 2: Deploy + Integrate with Main App

```python
# In api/main.py, add:
from api.routes.math_humans import router as math_humans_router
app.include_router(math_humans_router)
```

Then deploy your main application.

### Option 3: Learn More First

- Read: [HARMONYØ4_MATHEMATICAL_HUMANS.md](HARMONYØ4_MATHEMATICAL_HUMANS.md)
- Review: [PRODUCTION_DEPLOYMENT_GUIDE.md](PRODUCTION_DEPLOYMENT_GUIDE.md)
- Deep dive: [MATHEMATICAL_HUMAN_SYSTEM.md](MATHEMATICAL_HUMAN_SYSTEM.md)

---

## Files Location

```
humans/                     # Core system (6 modules)
api/routes/math_humans.py   # API endpoints
config/math_humans.env      # Configuration
scripts/deploy_math_humans.sh # Deployment
```

---

## System Status After Deployment

```
✅ Generation: Working
✅ Verification: Working
✅ Harm Prevention: Active
✅ Monitoring: Active
✅ All Endpoints: Live
✅ Documentation: Accessible

Status: PRODUCTION READY
```

---

## One-Liner to Deploy + Test

```bash
./scripts/deploy_math_humans.sh && sleep 5 && curl http://localhost:8000/math-humans/system-status | python -m json.tool
```

---

## Documentation Map

```
🟢 START HERE
   └─ HARMONYØ4_MATHEMATICAL_HUMANS.md
      └─ Overview + quick start

🟢 DEPLOYMENT
   └─ PRODUCTION_DEPLOYMENT_GUIDE.md
      └─ Complete deployment guide

🟢 DEEP DIVE
   └─ MATHEMATICAL_HUMAN_SYSTEM.md
      └─ Architecture + proofs

🟢 CODE
   └─ api/routes/math_humans.py
      └─ Implementation details

🟢 CHECKLIST
   └─ DEPLOYMENT_CHECKLIST.md
      └─ Verification steps

🟢 SUMMARY
   └─ FINAL_DELIVERY_SUMMARY.md
      └─ Complete overview
```

---

## Command Reference

```bash
# Deploy
./scripts/deploy_math_humans.sh

# Generate
curl -X POST http://localhost:8000/math-humans/generate \
  -H "Content-Type: application/json" \
  -d '{"method":"golden_ratio"}'

# Verify (replace HASH)
curl http://localhost:8000/math-humans/HASH/verify

# Check status
curl http://localhost:8000/math-humans/system-status

# Get philosophy
curl http://localhost:8000/math-humans/philosophy

# View logs
docker-compose -f docker-compose.geometry.yml logs -f

# Stop services
docker-compose -f docker-compose.geometry.yml down
```

---

## Expected Deployment Output

```
🔧 Deploying HarmonyØ4 Mathematical Humans...

✅ Checking dependencies...
✅ Generating cryptographic secrets...
✅ Building Docker images...
✅ Starting services...
✅ Waiting for services to be ready...
✅ Running generation test...
✅ Running verification test...
✅ Running harm prevention test...

╔─────────────────────────────────────╗
│   SYSTEM READY FOR PRODUCTION       │
│   All tests passed ✅               │
│                                     │
│   Endpoints:                        │
│   http://localhost:8000/math-humans │
│                                     │
│   Status: 🟢 OPERATIONAL            │
└─────────────────────────────────────╘
```

---

**Status**: ✅ READY TO DEPLOY

**Next Command**: `./scripts/deploy_math_humans.sh`

**Time to Production**: ~2 minutes
