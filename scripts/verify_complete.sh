#!/bin/bash
set -e

echo "🔍 HarmonyØ4 Geometry Generator - Complete Verification"
echo "======================================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
        return 0
    else
        echo -e "${RED}❌ $1${NC}"
        exit 1
    fi
}

echo ""
echo "Phase Verification:"
echo "─────────────────────────────────────────────────────────────"

# Check Phase G0
echo -n "Verifying Phase G0 (Geometry Spec)... "
python -c "from geometry.spec import GeometryToken, GeometryTokenType, create_primitive" 2>/dev/null
check "Phase G0 - Geometry Specification"

# Check Phase G1
echo -n "Verifying Phase G1 (Prompt Parser)... "
python -c "from generators.transformers.prompt_to_geometry import parse_prompt, analyze_prompt_complexity" 2>/dev/null
check "Phase G1 - Prompt Parser"

# Check Phase G2
echo -n "Verifying Phase G2 (Ethics Guard)... "
python -c "from ethics.constraints import GeometryEthicsGuard, validate_geometry, safe_validate_geometry" 2>/dev/null
check "Phase G2 - Ethics Guard"

# Check Phase G3
echo -n "Verifying Phase G3 (Temporal System)... "
python -c "from geometry.temporal import TemporalGeometryGenerator, TemporalSequence" 2>/dev/null
check "Phase G3 - Temporal System"

# Check Phase G4
echo -n "Verifying Phase G4 (Container Integration)... "
python -c "from container.geometry_container import GeometryContainer, create_geometry_container" 2>/dev/null
check "Phase G4 - Container Integration"

# Check Phase G5
echo -n "Verifying Phase G5 (API Endpoints)... "
python -c "from api.routes.geometry import router" 2>/dev/null
check "Phase G5 - API & Viewer"

echo ""
echo "Functional Tests:"
echo "─────────────────────────────────────────────────────────────"

# End-to-end test
echo "Running end-to-end workflow test..."
python -c "
from geometry.spec import create_primitive
from generators.transformers.prompt_to_geometry import parse_prompt
from ethics.constraints import safe_validate_geometry
from geometry.temporal import TemporalGeometryGenerator

# Test 1: Create primitive
print('  • Creating primitive geometry...')
cube = create_primitive('cube', size=2.0)
assert cube.uid.startswith('g'), 'UID generation failed'
print(f'    ✓ Cube created with UID: {cube.uid}')

# Test 2: Parse prompt
print('  • Parsing natural language prompt...')
tokens = parse_prompt('large rotating cube')
assert len(tokens) >= 1, 'Prompt parsing failed'
print(f'    ✓ Parsed {len(tokens)} tokens')

# Test 3: Validate ethics
print('  • Running ethics validation...')
report = safe_validate_geometry(tokens)
assert report['valid'], 'Ethics validation failed'
print(f'    ✓ All {report[\"token_count\"]} tokens passed ethics checks')

# Test 4: Create animation
print('  • Generating temporal animation...')
generator = TemporalGeometryGenerator(fps=30)
sequences = generator.create_animation([cube], duration_seconds=2.0)
assert len(sequences) > 0, 'Animation generation failed'
assert sequences[0].duration_frames == 60, 'Frame count incorrect'
print(f'    ✓ Created {len(sequences)} animation sequences ({sequences[0].duration_frames} frames)')

# Test 5: Forbidden content rejection
print('  • Testing forbidden content rejection...')
try:
    parse_prompt('human face')
    print('    ✗ FAILED: Should have rejected forbidden content')
    exit(1)
except ValueError as e:
    print('    ✓ Correctly rejected forbidden content')

print()
print('🎉 All functional tests passed!')
" 2>&1
check "End-to-end functionality"

echo ""
echo "File Structure Check:"
echo "─────────────────────────────────────────────────────────────"

# Check key files exist
files_to_check=(
    "geometry/spec.py"
    "geometry/temporal.py"
    "generators/transformers/prompt_to_geometry.py"
    "ethics/constraints.py"
    "container/geometry_container.py"
    "api/routes/geometry.py"
    "docker-compose.geometry.yml"
    "Dockerfile.geometry"
    "requirements_complete.txt"
    "GEOMETRY_IMPLEMENTATION.md"
    "GEOMETRY_QUICK_START.md"
)

for file in "${files_to_check[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file (missing)"
        exit 1
    fi
done

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              ✅ VERIFICATION COMPLETE!                        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "System Status:"
echo "  • All 6 phases (G0-G5) verified successfully"
echo "  • All functional tests passed"
echo "  • All required files present"
echo "  • Ready for production deployment"
echo ""
echo "Next Steps:"
echo "  1. Review deployment configuration"
echo "  2. Run: ./scripts/deploy_production.sh"
echo "  3. Monitor: docker-compose -f docker-compose.geometry.yml logs -f"
echo ""
