#!/bin/bash
set -e

echo "🔒 HarmonyØ4 Geometry Generator - Production Security Audit"
echo "==========================================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNINGS=0

check_pass() {
    echo -e "${GREEN}✅ $1${NC}"
    PASSED_CHECKS=$((PASSED_CHECKS+1))
    TOTAL_CHECKS=$((TOTAL_CHECKS+1))
}

check_fail() {
    echo -e "${RED}❌ $1${NC}"
    FAILED_CHECKS=$((FAILED_CHECKS+1))
    TOTAL_CHECKS=$((TOTAL_CHECKS+1))
}

check_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    WARNINGS=$((WARNINGS+1))
}

echo "1. Credential Security"
echo "────────────────────────────────────────────────────────────"

# Check for default passwords
if grep -rq "password123\|admin123\|changeme\|CHANGEME" config/*.env 2>/dev/null; then
    check_fail "Default passwords detected in config files"
else
    check_pass "No default passwords found"
fi

# Check for hardcoded secrets in code
if grep -rq "password\s*=\s*['\"][^'\"]\+['\"]" api/ generators/ 2>/dev/null; then
    check_warn "Potential hardcoded passwords in source code"
fi

# Check environment file permissions
if [ -f config/production.env ]; then
    PERMS=$(stat -c %a config/production.env 2>/dev/null || stat -f %A config/production.env 2>/dev/null)
    if [ "$PERMS" = "600" ] || [ "$PERMS" = "400" ]; then
        check_pass "Environment file has secure permissions ($PERMS)"
    else
        check_warn "Environment file permissions should be 600 or 400 (currently: $PERMS)"
    fi
fi

echo ""
echo "2. Docker Security"
echo "────────────────────────────────────────────────────────────"

# Check for privileged containers
if grep -q "privileged:\s*true" docker-compose.geometry.yml; then
    check_fail "Privileged containers detected"
else
    check_pass "No privileged containers"
fi

# Check for host network mode
if grep -q "network_mode:\s*host" docker-compose.geometry.yml; then
    check_fail "Host network mode detected"
else
    check_pass "No host network mode"
fi

# Check for root user
if grep -q "user:\s*root\|user:\s*0" docker-compose.geometry.yml; then
    check_warn "Container running as root user"
else
    check_pass "Containers not running as root"
fi

# Check for sensitive volume mounts
if grep -q ":/root\|:/etc/passwd\|:/etc/shadow" docker-compose.geometry.yml; then
    check_fail "Sensitive host paths mounted"
else
    check_pass "No sensitive host paths mounted"
fi

echo ""
echo "3. Network Security"
echo "────────────────────────────────────────────────────────────"

# Check exposed ports
EXPOSED_PORTS=$(grep -E "^\s*-\s*\"[0-9]" docker-compose.geometry.yml | wc -l)
if [ $EXPOSED_PORTS -gt 5 ]; then
    check_warn "$EXPOSED_PORTS ports exposed - review for necessity"
else
    check_pass "Port exposure is minimal ($EXPOSED_PORTS ports)"
fi

# Check for 0.0.0.0 bindings
if grep -q "0\.0\.0\.0" docker-compose.geometry.yml; then
    check_warn "Services binding to 0.0.0.0 - ensure firewall is configured"
fi

echo ""
echo "4. Application Security"
echo "────────────────────────────────────────────────────────────"

# Check ethics strict mode
if [ -f config/production.env ]; then
    if grep -q "ETHICS_STRICT_MODE=true" config/production.env; then
        check_pass "Ethics strict mode enabled"
    else
        check_fail "Ethics strict mode not enabled"
    fi
fi

# Check rate limiting
if [ -f config/production.env ]; then
    if grep -q "RATE_LIMIT_ENABLED=true" config/production.env; then
        check_pass "Rate limiting enabled"
    else
        check_warn "Rate limiting not enabled"
    fi
fi

# Check for debug mode
if grep -rq "DEBUG\s*=\s*True\|debug\s*=\s*true" api/ config/ 2>/dev/null; then
    check_fail "Debug mode enabled in production"
else
    check_pass "Debug mode disabled"
fi

echo ""
echo "5. Dependency Security"
echo "────────────────────────────────────────────────────────────"

# Check for outdated dependencies (if pip-audit available)
if command -v pip-audit >/dev/null 2>&1; then
    if pip-audit -r requirements_complete.txt >/dev/null 2>&1; then
        check_pass "No known vulnerabilities in dependencies"
    else
        check_warn "Vulnerabilities detected in dependencies - run 'pip-audit -r requirements_complete.txt'"
    fi
else
    check_warn "pip-audit not installed - cannot check dependency vulnerabilities"
fi

echo ""
echo "6. API Security Headers"
echo "────────────────────────────────────────────────────────────"

# Check nginx security headers
if [ -f config/nginx-viewer.conf ]; then
    if grep -q "X-Frame-Options\|X-Content-Type-Options\|X-XSS-Protection" config/nginx-viewer.conf; then
        check_pass "Security headers configured in nginx"
    else
        check_warn "Security headers not configured in nginx"
    fi
fi

# Check CORS configuration
if [ -f config/production.env ]; then
    if grep -q "ALLOWED_ORIGINS=.*\*" config/production.env; then
        check_warn "CORS allows all origins - tighten for production"
    else
        check_pass "CORS configured with specific origins"
    fi
fi

echo ""
echo "7. Data Protection"
echo "────────────────────────────────────────────────────────────"

# Check for backup configuration
if [ -f scripts/backup.sh ]; then
    check_pass "Backup script present"
else
    check_warn "Backup script not found"
fi

# Check for SSL/TLS configuration
if grep -q "ssl_certificate\|SSL_CERT" config/ docker-compose.geometry.yml 2>/dev/null; then
    check_pass "SSL/TLS configuration detected"
else
    check_warn "No SSL/TLS configuration - use reverse proxy for HTTPS"
fi

echo ""
echo "=========================================================="
echo "📊 Security Audit Results:"
echo "=========================================================="
echo -e "Total Checks:   ${TOTAL_CHECKS}"
echo -e "Passed:         ${GREEN}${PASSED_CHECKS}${NC}"
echo -e "Failed:         ${RED}${FAILED_CHECKS}${NC}"
echo -e "Warnings:       ${YELLOW}${WARNINGS}${NC}"
echo ""

if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "${GREEN}✅ Security audit passed!${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Address warnings before production deployment${NC}"
    fi
    exit 0
else
    echo -e "${RED}❌ Security audit failed - fix critical issues before deployment${NC}"
    exit 1
fi
