#!/bin/bash
# Real-time production monitoring dashboard

COMPOSE_FILE="docker-compose.geometry.yml"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

clear

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       HarmonyØ4 Geometry Generator - Production Monitor                     ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Container Status
echo -e "${GREEN}📦 Container Status:${NC}"
echo "────────────────────────────────────────────────────────────"
docker-compose -f $COMPOSE_FILE ps 2>/dev/null || echo "Docker Compose unavailable"
echo ""

# API Health
echo -e "${GREEN}📊 API Health:${NC}"
echo "────────────────────────────────────────────────────────────"
HEALTH=$(curl -s http://localhost:8000/geometry/health 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"
else
    echo -e "${RED}❌ API Unavailable${NC}"
fi
echo ""

# Database Status
echo -e "${GREEN}🗄️ Database:${NC}"
echo "────────────────────────────────────────────────────────────"
DB_RESULT=$(docker-compose -f $COMPOSE_FILE exec -T db psql -U harmony -d harmony4 -c "
    SELECT 
        'Connections: ' || count(*) as connections
    FROM pg_stat_activity 
    WHERE datname = 'harmony4';" 2>/dev/null | grep "Connections" || echo "Database unavailable")
echo "$DB_RESULT"
echo ""

# Redis Status
echo -e "${GREEN}💾 Redis Cache:${NC}"
echo "────────────────────────────────────────────────────────────"
REDIS_INFO=$(docker-compose -f $COMPOSE_FILE exec -T redis redis-cli INFO stats 2>/dev/null | grep "total_commands_processed\|keyspace_hits\|keyspace_misses" || echo "Redis unavailable")
echo "$REDIS_INFO"
echo ""

# System Resources
echo -e "${GREEN}🔧 System Resources:${NC}"
echo "────────────────────────────────────────────────────────────"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" \
    $(docker-compose -f $COMPOSE_FILE ps -q 2>/dev/null) 2>/dev/null || echo "Stats unavailable"
echo ""

# Recent Logs
echo -e "${GREEN}📝 Recent Activity (last 5 entries):${NC}"
echo "────────────────────────────────────────────────────────────"
docker-compose -f $COMPOSE_FILE logs --tail=5 harmony4-api 2>/dev/null | tail -5 || echo "Logs unavailable"
echo ""

# Quick Stats
echo -e "${GREEN}📈 Quick Stats:${NC}"
echo "────────────────────────────────────────────────────────────"
METRICS=$(curl -s http://localhost:8000/geometry/primitives 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "Primitives available: $(echo $METRICS | python3 -c 'import sys, json; data=json.load(sys.stdin); print(len(data.get("primitives", [])))' 2>/dev/null || echo 'N/A')"
else
    echo "Metrics unavailable"
fi
echo ""

echo -e "${BLUE}Press Ctrl+C to exit | Refresh: every 5 seconds${NC}"
