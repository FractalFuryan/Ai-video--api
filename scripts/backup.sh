#!/bin/bash
set -e

# HarmonyØ4 Geometry Generator - Complete System Backup
BACKUP_ROOT="${BACKUP_ROOT:-/backups/harmony4}"
BACKUP_DIR="$BACKUP_ROOT/$(date +%Y%m%d_%H%M%S)"
COMPOSE_FILE="docker-compose.geometry.yml"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           HarmonyØ4 Geometry Generator - System Backup                      ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"
echo -e "${GREEN}📁 Backup directory: $BACKUP_DIR${NC}"
echo ""

# 1. Backup database
echo -e "${GREEN}🗄️  Backing up database...${NC}"
docker-compose -f $COMPOSE_FILE exec -T db \
    pg_dump -U harmony -Fc harmony4 > "$BACKUP_DIR/database.dump"

# Also create SQL version for easy inspection
docker-compose -f $COMPOSE_FILE exec -T db \
    pg_dump -U harmony harmony4 > "$BACKUP_DIR/database.sql"

echo "   ✓ Database backed up ($(du -h $BACKUP_DIR/database.dump | cut -f1))"
echo ""

# 2. Backup Redis data
echo -e "${GREEN}💾 Backing up Redis cache...${NC}"
docker-compose -f $COMPOSE_FILE exec -T redis \
    redis-cli --rdb /data/backup.rdb > /dev/null 2>&1 || true
docker cp $(docker-compose -f $COMPOSE_FILE ps -q redis):/data/backup.rdb "$BACKUP_DIR/redis.rdb" 2>/dev/null || echo "   ⚠ Redis backup skipped"
echo "   ✓ Redis backed up"
echo ""

# 3. Backup configuration
echo -e "${GREEN}⚙️  Backing up configuration...${NC}"
mkdir -p "$BACKUP_DIR/config"
cp -r config/* "$BACKUP_DIR/config/" 2>/dev/null || true
cp docker-compose.geometry.yml "$BACKUP_DIR/"
cp Dockerfile.geometry "$BACKUP_DIR/"
cp requirements_complete.txt "$BACKUP_DIR/"
echo "   ✓ Configuration backed up ($(find $BACKUP_DIR/config -type f | wc -l) files)"
echo ""

# 4. Backup application code
echo -e "${GREEN}💻 Backing up application code...${NC}"
mkdir -p "$BACKUP_DIR/src"
for dir in api geometry generators ethics container utils; do
    if [ -d "$dir" ]; then
        cp -r "$dir" "$BACKUP_DIR/src/"
    fi
done
echo "   ✓ Application code backed up"
echo ""

# 5. Backup storage/containers
echo -e "${GREEN}📦 Backing up geometry containers...${NC}"
if [ -d "storage/containers" ]; then
    mkdir -p "$BACKUP_DIR/storage"
    cp -r storage/containers "$BACKUP_DIR/storage/" 2>/dev/null || true
    CONTAINER_COUNT=$(find storage/containers -type f 2>/dev/null | wc -l)
    echo "   ✓ Backed up $CONTAINER_COUNT geometry containers"
else
    echo "   ⚠ No containers to backup"
fi
echo ""

# 6. Backup logs
echo -e "${GREEN}📝 Backing up logs...${NC}"
if [ -d "logs" ]; then
    mkdir -p "$BACKUP_DIR/logs"
    # Only backup last 7 days of logs to save space
    find logs -type f -mtime -7 -exec cp {} "$BACKUP_DIR/logs/" \; 2>/dev/null || true
    echo "   ✓ Logs backed up"
else
    echo "   ⚠ No logs to backup"
fi
echo ""

# 7. Create backup manifest
echo -e "${GREEN}📋 Creating backup manifest...${NC}"
cat > "$BACKUP_DIR/MANIFEST.md" << EOF
# HarmonyØ4 Geometry Generator - Backup Manifest

## Backup Information
- **Date:** $(date)
- **Version:** 1.0.0
- **Backup ID:** $(basename $BACKUP_DIR)

## Components Backed Up

### Database
- Format: PostgreSQL custom dump + SQL
- Size: $(du -h $BACKUP_DIR/database.dump | cut -f1)
- Lines: $(wc -l $BACKUP_DIR/database.sql | awk '{print $1}')

### Configuration
- Files: $(find $BACKUP_DIR/config -type f | wc -l)
- Includes: environment, nginx, docker-compose

### Application Code
- Directories: $(find $BACKUP_DIR/src -type d | wc -l)
- Files: $(find $BACKUP_DIR/src -type f | wc -l)

### Geometry Containers
- Count: $(find $BACKUP_DIR/storage/containers -type f 2>/dev/null | wc -l || echo 0)
- Location: storage/containers/

### Logs
- Files: $(find $BACKUP_DIR/logs -type f 2>/dev/null | wc -l || echo 0)
- Period: Last 7 days

## Restoration

To restore this backup:

\`\`\`bash
./scripts/restore.sh $BACKUP_DIR
\`\`\`

## Verification

Backup integrity can be verified with:

\`\`\`bash
# Verify database dump
pg_restore --list $BACKUP_DIR/database.dump | wc -l

# Verify file checksums
cd $BACKUP_DIR && sha256sum -c checksums.txt
\`\`\`
EOF

# Create checksums
echo -e "${GREEN}🔐 Creating checksums...${NC}"
cd "$BACKUP_DIR"
find . -type f ! -name "checksums.txt" -exec sha256sum {} \; > checksums.txt
cd - > /dev/null
echo "   ✓ Checksums created"
echo ""

# Calculate total backup size
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                        ✅ BACKUP COMPLETE!                                  ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Backup Location: $BACKUP_DIR"
echo "Total Size: $TOTAL_SIZE"
echo ""
echo "To restore: ./scripts/restore.sh $BACKUP_DIR"
echo "To verify:  sha256sum -c $BACKUP_DIR/checksums.txt"
echo ""

# Create symlink to latest backup
ln -sfn "$BACKUP_DIR" "$BACKUP_ROOT/latest"
echo "Latest backup symlink updated: $BACKUP_ROOT/latest"
echo ""
