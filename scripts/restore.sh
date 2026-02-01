#!/bin/bash
set -e

# HarmonyØ4 Geometry Generator - System Restoration
BACKUP_DIR=$1
COMPOSE_FILE="docker-compose.geometry.yml"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

if [ -z "$BACKUP_DIR" ] || [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${RED}Usage: $0 <backup_directory>${NC}"
    echo ""
    echo "Available backups:"
    ls -lth /backups/harmony4/ 2>/dev/null | grep "^d" | head -5 || echo "No backups found"
    exit 1
fi

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           HarmonyØ4 Geometry Generator - System Restoration                 ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}⚠️  WARNING: This will replace all current data!${NC}"
echo ""
echo "Backup source: $BACKUP_DIR"
echo "Backup date: $(basename $BACKUP_DIR)"
echo ""
read -p "Continue with restoration? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restoration cancelled."
    exit 0
fi

echo ""
echo -e "${GREEN}Starting restoration...${NC}"
echo ""

# 1. Stop all services
echo -e "${GREEN}🛑 Stopping services...${NC}"
docker-compose -f $COMPOSE_FILE down
echo "   ✓ Services stopped"
echo ""

# 2. Start only database for restoration
echo -e "${GREEN}🗄️  Starting database for restoration...${NC}"
docker-compose -f $COMPOSE_FILE up -d db
sleep 10  # Wait for database to be ready

# Wait for database to be ready
for i in {1..30}; do
    if docker-compose -f $COMPOSE_FILE exec -T db pg_isready -U harmony >/dev/null 2>&1; then
        echo "   ✓ Database ready"
        break
    fi
    sleep 2
done
echo ""

# 3. Drop and recreate database
echo -e "${GREEN}🔄 Recreating database...${NC}"
docker-compose -f $COMPOSE_FILE exec -T db psql -U harmony -c "DROP DATABASE IF EXISTS harmony4;" postgres
docker-compose -f $COMPOSE_FILE exec -T db psql -U harmony -c "CREATE DATABASE harmony4;" postgres
echo "   ✓ Database recreated"
echo ""

# 4. Restore database
echo -e "${GREEN}📥 Restoring database...${NC}"
if [ -f "$BACKUP_DIR/database.dump" ]; then
    # Restore from custom dump (preferred)
    cat "$BACKUP_DIR/database.dump" | docker-compose -f $COMPOSE_FILE exec -T db \
        pg_restore -U harmony -d harmony4 --no-owner --no-acl 2>/dev/null || true
    echo "   ✓ Database restored from dump"
elif [ -f "$BACKUP_DIR/database.sql" ]; then
    # Restore from SQL
    cat "$BACKUP_DIR/database.sql" | docker-compose -f $COMPOSE_FILE exec -T db \
        psql -U harmony harmony4
    echo "   ✓ Database restored from SQL"
else
    echo -e "   ${RED}✗ No database backup found${NC}"
fi
echo ""

# 5. Stop database
docker-compose -f $COMPOSE_FILE down
echo ""

# 6. Restore configuration
echo -e "${GREEN}⚙️  Restoring configuration...${NC}"
if [ -d "$BACKUP_DIR/config" ]; then
    mkdir -p config
    cp -r "$BACKUP_DIR/config/"* config/ 2>/dev/null || true
    echo "   ✓ Configuration restored"
else
    echo -e "   ${YELLOW}⚠ No configuration backup found${NC}"
fi
echo ""

# 7. Restore application code (optional)
echo -e "${GREEN}💻 Restoring application code...${NC}"
if [ -d "$BACKUP_DIR/src" ]; then
    read -p "Restore application code? This will overwrite current code (yes/no): " RESTORE_CODE
    if [ "$RESTORE_CODE" = "yes" ]; then
        cp -r "$BACKUP_DIR/src/"* . 2>/dev/null || true
        echo "   ✓ Application code restored"
    else
        echo "   ⊘ Application code restoration skipped"
    fi
else
    echo -e "   ${YELLOW}⚠ No application code backup found${NC}"
fi
echo ""

# 8. Restore geometry containers
echo -e "${GREEN}📦 Restoring geometry containers...${NC}"
if [ -d "$BACKUP_DIR/storage/containers" ]; then
    mkdir -p storage/containers
    cp -r "$BACKUP_DIR/storage/containers/"* storage/containers/ 2>/dev/null || true
    RESTORED_CONTAINERS=$(find storage/containers -type f 2>/dev/null | wc -l)
    echo "   ✓ Restored $RESTORED_CONTAINERS containers"
else
    echo -e "   ${YELLOW}⚠ No containers backup found${NC}"
fi
echo ""

# 9. Start all services
echo -e "${GREEN}🚀 Starting all services...${NC}"
docker-compose -f $COMPOSE_FILE up -d
echo "   ✓ Services starting..."
echo ""

# 10. Wait for services and verify
echo -e "${GREEN}🔍 Waiting for services to be healthy...${NC}"
sleep 15

for i in {1..30}; do
    if curl -s http://localhost:8000/geometry/health >/dev/null 2>&1; then
        echo "   ✓ API is healthy"
        break
    fi
    sleep 2
done
echo ""

# 11. Verify restoration
echo -e "${GREEN}✅ Verifying restoration...${NC}"

# Check database
DB_CHECK=$(docker-compose -f $COMPOSE_FILE exec -T db psql -U harmony -d harmony4 \
    -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | grep -o "[0-9]\+" | head -1 || echo "0")
echo "   Database tables: $DB_CHECK"

# Check API
if curl -s http://localhost:8000/geometry/health | grep -q "ok\|healthy"; then
    echo "   API health: OK"
else
    echo -e "   ${YELLOW}API health: Check manually${NC}"
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                      ✅ RESTORATION COMPLETE!                               ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Restored from: $BACKUP_DIR"
echo "Services status: docker-compose -f $COMPOSE_FILE ps"
echo "View logs: docker-compose -f $COMPOSE_FILE logs -f"
echo ""
echo "Verify the system:"
echo "  - API: http://localhost:8000/geometry/health"
echo "  - Viewer: http://localhost:8080/health"
echo ""
