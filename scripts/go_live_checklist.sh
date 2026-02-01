#!/bin/bash
set -e

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║       🎯 HarmonyØ4 Geometry Generator - Go-Live Checklist                  ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

TOTAL=0
PASSED=0
FAILED=0
WARNINGS=0

check() {
    TOTAL=$((TOTAL+1))
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
        PASSED=$((PASSED+1))
        return 0
    else
        echo -e "${RED}❌ $1${NC}"
        FAILED=$((FAILED+1))
        return 1
    fi
}

warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    WARNINGS=$((WARNINGS+1))
}

section() {
    echo ""
    echo -e "${BLUE}$1${NC}"
    echo "────────────────────────────────────────────────────────────"
}

section "1. Infrastructure Prerequisites"

command -v docker >/dev/null 2>&1
check "Docker installed ($(docker --version 2>/dev/null | cut -d' ' -f3 | cut -d',' -f1))"

command -v docker-compose >/dev/null 2>&1
check "Docker Compose installed ($(docker-compose --version 2>/dev/null | cut -d' ' -f3 | cut -d',' -f1))"

docker info >/dev/null 2>&1
check "Docker daemon running"

section "2. Security Configuration"

if [ -f config/production.env ]; then
    if ! grep -q "CHANGEME" config/production.env; then
        check "Production environment configured"
    else
        echo -e "${RED}❌ Production environment contains default values${NC}"
        FAILED=$((FAILED+1))
        TOTAL=$((TOTAL+1))
    fi
else
    echo -e "${YELLOW}⚠️  Production environment file not found - using defaults${NC}"
    warn "Create config/production.env from config/production.env.example"
fi

# Check for secure password generation
if [ -f config/production.env ] && grep -q "POSTGRES_PASSWORD=.*[A-Za-z0-9]{32}" config/production.env; then
    check "Database password is strong"
else
    warn "Generate strong database password: openssl rand -hex 32"
fi

# Check JWT secret
if [ -f config/production.env ] && grep -q "JWT_SECRET=.*[A-Za-z0-9]{64}" config/production.env; then
    check "JWT secret is configured"
else
    warn "Generate JWT secret: openssl rand -hex 64"
fi

section "3. Required Files"

files=(
    "docker-compose.geometry.yml:Docker Compose configuration"
    "Dockerfile.geometry:Production Dockerfile"
    "requirements_complete.txt:Python dependencies"
    "scripts/deploy_production.sh:Deployment script"
    "scripts/verify_complete.sh:Verification script"
)

for item in "${files[@]}"; do
    file="${item%%:*}"
    desc="${item##*:}"
    [ -f "$file" ]
    check "$desc ($file)"
done

section "4. Core Application Modules"

modules=(
    "geometry/spec.py"
    "generators/transformers/prompt_to_geometry.py"
    "ethics/constraints.py"
    "geometry/temporal.py"
    "container/geometry_container.py"
    "api/routes/geometry.py"
)

for module in "${modules[@]}"; do
    [ -f "$module" ]
    check "$(basename $module) module present"
done

section "5. Service Deployment"

# Deploy services if not running
if ! docker-compose -f docker-compose.geometry.yml ps | grep -q "Up"; then
    echo "Starting services for verification..."
    ./scripts/deploy_production.sh >/dev/null 2>&1 &
    sleep 20
fi

# Check if services are running
docker-compose -f docker-compose.geometry.yml ps | grep -q "harmony4-api.*Up"
check "API service running"

docker-compose -f docker-compose.geometry.yml ps | grep -q "harmony4-db.*Up"
check "Database service running"

docker-compose -f docker-compose.geometry.yml ps | grep -q "harmony4-redis.*Up"
check "Redis service running"

section "6. Health Checks"

# Wait a bit for services to be fully ready
sleep 10

# API health
if curl -s -f http://localhost:8000/geometry/health >/dev/null 2>&1; then
    HEALTH_STATUS=$(curl -s http://localhost:8000/geometry/health | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null || echo "unknown")
    if [ "$HEALTH_STATUS" = "ok" ] || [ "$HEALTH_STATUS" = "healthy" ]; then
        check "API health endpoint responding (status: $HEALTH_STATUS)"
    else
        echo -e "${RED}❌ API health check failed (status: $HEALTH_STATUS)${NC}"
        FAILED=$((FAILED+1))
        TOTAL=$((TOTAL+1))
    fi
else
    echo -e "${RED}❌ API health endpoint not accessible${NC}"
    FAILED=$((FAILED+1))
    TOTAL=$((TOTAL+1))
fi

# Database health
docker-compose -f docker-compose.geometry.yml exec -T db pg_isready -U harmony >/dev/null 2>&1
check "Database connection healthy"

# Redis health
docker-compose -f docker-compose.geometry.yml exec -T redis redis-cli ping >/dev/null 2>&1
check "Redis connection healthy"

# Viewer CDN (if running)
if docker-compose -f docker-compose.geometry.yml ps | grep -q "viewer-cdn.*Up"; then
    curl -s -f http://localhost:8080/health >/dev/null 2>&1
    check "Viewer CDN responding"
fi

section "7. Functional Tests"

# Test primitives endpoint
curl -s http://localhost:8000/geometry/primitives | grep -q "cube" 2>/dev/null
check "Primitives endpoint functional"

# Test generation endpoint
RESPONSE=$(curl -s -X POST http://localhost:8000/geometry/generate \
    -H "Content-Type: application/json" \
    -d '{"prompt": "test cube"}' 2>/dev/null)

echo "$RESPONSE" | grep -q "tokens" 2>/dev/null
check "Geometry generation functional"

# Test ethics validation
FORBIDDEN_RESPONSE=$(curl -s -X POST http://localhost:8000/geometry/generate \
    -H "Content-Type: application/json" \
    -d '{"prompt": "human face"}' 2>/dev/null)

if echo "$FORBIDDEN_RESPONSE" | grep -qi "forbidden\|rejected\|error" 2>/dev/null; then
    check "Ethics validation working (forbidden content rejected)"
else
    warn "Ethics validation may need review"
fi

section "8. Documentation"

[ -f "GEOMETRY_IMPLEMENTATION.md" ]
check "Implementation documentation present"

[ -f "GEOMETRY_QUICK_START.md" ]
check "Quick start guide present"

[ -f "DEPLOYMENT_MANIFEST.md" ]
check "Deployment manifest present"

section "9. Operations Scripts"

scripts=(
    "scripts/backup.sh:Backup script"
    "scripts/restore.sh:Restore script"
    "scripts/monitoring.sh:Monitoring script"
    "scripts/security_audit.sh:Security audit"
)

for item in "${scripts[@]}"; do
    script="${item%%:*}"
    desc="${item##*:}"
    [ -f "$script" ] && [ -x "$script" ]
    check "$desc executable"
done

section "10. Production Readiness"

# Check ethics strict mode
if [ -f config/production.env ] && grep -q "ETHICS_STRICT_MODE=true" config/production.env; then
    check "Ethics strict mode enabled"
else
    warn "Enable ethics strict mode in config/production.env"
fi

# Check rate limiting
if [ -f config/production.env ] && grep -q "RATE_LIMIT_ENABLED=true" config/production.env; then
    check "Rate limiting enabled"
else
    warn "Enable rate limiting in config/production.env"
fi

# Check logging level
if [ -f config/production.env ]; then
    LOG_LEVEL=$(grep "LOG_LEVEL=" config/production.env | cut -d'=' -f2)
    if [ "$LOG_LEVEL" = "INFO" ] || [ "$LOG_LEVEL" = "WARNING" ]; then
        check "Logging level appropriate for production ($LOG_LEVEL)"
    else
        warn "Consider setting LOG_LEVEL=INFO for production"
    fi
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "📊 GO-LIVE CHECKLIST RESULTS"
echo "════════════════════════════════════════════════════════════"
printf "Total Checks:  %d\n" $TOTAL
printf "Passed:        ${GREEN}%d${NC}\n" $PASSED
printf "Failed:        ${RED}%d${NC}\n" $FAILED
printf "Warnings:      ${YELLOW}%d${NC}\n" $WARNINGS
echo ""

# Calculate percentage
if [ $TOTAL -gt 0 ]; then
    PERCENTAGE=$((PASSED * 100 / TOTAL))
    echo "Success Rate:  ${PERCENTAGE}%"
    echo ""
fi

if [ $FAILED -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                   🎉 SYSTEM READY FOR PRODUCTION! 🎉                         ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review the configuration in config/production.env"
    echo "  2. Set up SSL/TLS certificates for HTTPS"
    echo "  3. Configure your domain DNS"
    echo "  4. Deploy: ./scripts/deploy_production.sh production"
    echo "  5. Monitor: ./scripts/monitoring.sh"
    echo ""
    exit 0
elif [ $FAILED -eq 0 ]; then
    echo -e "${YELLOW}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║              ⚠️  SYSTEM READY - ADDRESS WARNINGS FIRST ⚠️                   ║${NC}"
    echo -e "${YELLOW}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Review the warnings above before production deployment."
    echo ""
    exit 0
else
    echo -e "${RED}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                ❌ SYSTEM NOT READY FOR PRODUCTION ❌                         ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Fix the failed checks above before deployment."
    echo ""
    exit 1
fi
