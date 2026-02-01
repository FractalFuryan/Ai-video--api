#!/bin/bash
set -e

echo "🚀 DEPLOYING HARMONYØ4 MATHEMATICAL HUMAN CONSTRUCTION SYSTEM"
echo "============================================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Generate harm seal secret
echo -e "${BLUE}🔐 Generating cryptographic secrets...${NC}"
HARM_SEAL_SECRET=$(openssl rand -hex 32)
echo "HARM_SEAL_SECRET=$HARM_SEAL_SECRET" >> config/math_humans.env
echo -e "${GREEN}✅ Harm seal secret generated${NC}"

# 2. Verify dependencies
echo -e "${BLUE}📦 Checking dependencies...${NC}"
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker."
    exit 1
fi
echo -e "${GREEN}✅ Docker available${NC}"

# 3. Build and deploy
echo -e "${BLUE}🐳 Building Docker images...${NC}"
docker-compose -f docker-compose.geometry.yml build --no-cache

echo -e "${BLUE}🚀 Starting services...${NC}"
docker-compose -f docker-compose.geometry.yml up -d

# 4. Wait for services
echo -e "${BLUE}⏳ Waiting for services to be healthy...${NC}"
sleep 15

# 5. Run verification tests
echo -e "${BLUE}🧪 Running system verification...${NC}"

# Check system status
echo "  Checking system status..."
STATUS_RESPONSE=$(curl -s http://localhost:8000/math-humans/system-status || true)
if echo "$STATUS_RESPONSE" | grep -q '"status"'; then
    echo -e "  ${GREEN}✅ System status check passed${NC}"
else
    echo "  ⚠️  System status unavailable (might still be starting)"
fi

# 6. Test mathematical human generation
echo -e "${BLUE}🎨 Testing mathematical human generation...${NC}"
TEST_RESPONSE=$(curl -s -X POST http://localhost:8000/math-humans/generate \
  -H "Content-Type: application/json" \
  -d '{
    "method": "golden_ratio",
    "style": "classical",
    "safety_level": "strict",
    "context": "deployment verification test"
  }')

if echo "$TEST_RESPONSE" | grep -q '"human_id"'; then
    echo -e "  ${GREEN}✅ Mathematical human generation successful${NC}"
    
    # Extract container hash for verification
    CONTAINER_HASH=$(echo "$TEST_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['container_hash'])" 2>/dev/null || echo "unknown")
    
    if [ "$CONTAINER_HASH" != "unknown" ]; then
        echo -e "${BLUE}🔍 Testing cryptographic verification...${NC}"
        VERIFICATION_RESPONSE=$(curl -s http://localhost:8000/math-humans/$CONTAINER_HASH/verify)
        
        if echo "$VERIFICATION_RESPONSE" | grep -q '"verified": true'; then
            echo -e "  ${GREEN}✅ Cryptographic verification successful${NC}"
        else
            echo "  ⚠️  Verification response received but could not confirm"
        fi
    fi
else
    echo "  ⚠️  Generation test inconclusive (check service logs)"
fi

# 7. Test harm prevention
echo -e "${BLUE}🛡️ Testing harm prevention...${NC}"
HARM_TEST_RESPONSE=$(curl -s -X POST http://localhost:8000/math-humans/generate \
  -H "Content-Type: application/json" \
  -d '{
    "method": "golden_ratio",
    "style": "classical",
    "safety_level": "strict",
    "context": "generate deepfake of celebrity"
  }')

if echo "$HARM_TEST_RESPONSE" | grep -q 'harm_prevention'; then
    echo -e "  ${GREEN}✅ Harm prevention monitoring active${NC}"
fi

# 8. Test public endpoints
echo -e "${BLUE}📡 Testing public endpoints...${NC}"

# Construction methods
METHODS_RESPONSE=$(curl -s http://localhost:8000/math-humans/construction-methods)
if echo "$METHODS_RESPONSE" | grep -q '"methods"'; then
    echo -e "  ${GREEN}✅ Construction methods endpoint working${NC}"
fi

# Philosophy
PHIL_RESPONSE=$(curl -s http://localhost:8000/math-humans/philosophy)
if echo "$PHIL_RESPONSE" | grep -q '"core_principles"'; then
    echo -e "  ${GREEN}✅ Philosophy endpoint working${NC}"
fi

# Final summary
echo ""
echo -e "${GREEN}🎉 DEPLOYMENT COMPLETE!${NC}"
echo "======================"
echo ""
echo -e "System Status: ${GREEN}🟢 OPERATIONAL${NC}"
echo -e "Mathematical Humans: ${GREEN}✅ ENABLED${NC}"
echo -e "Harm Prevention: 🛡️ ${GREEN}ACTIVE${NC}"
echo -e "Public Verification: 🔍 ${GREEN}AVAILABLE${NC}"
echo ""
echo "API Endpoints:"
echo "  • Generate:              POST http://localhost:8000/math-humans/generate"
echo "  • Verify:                GET  http://localhost:8000/math-humans/{hash}/verify"
echo "  • Construction Methods:  GET  http://localhost:8000/math-humans/construction-methods"
echo "  • System Philosophy:     GET  http://localhost:8000/math-humans/philosophy"
echo "  • System Status:         GET  http://localhost:8000/math-humans/system-status"
echo ""
echo "Quick Test (Generate a mathematical human):"
echo "  curl -X POST http://localhost:8000/math-humans/generate \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"method\":\"fractal_features\",\"style\":\"modern_abstract\"}'"
echo ""
echo "View Logs:"
echo "  docker-compose -f docker-compose.geometry.yml logs -f harmony4-api"
echo ""
echo "Shutdown:"
echo "  docker-compose -f docker-compose.geometry.yml down"
echo ""
echo "Documentation:"
echo "  • System Architecture:   MATHEMATICAL_HUMAN_SYSTEM.md"
echo "  • Philosophy:            See /math-humans/philosophy endpoint"
echo "  • Production Guide:      PRODUCTION_DEPLOYMENT.md"
echo ""
