# HarmonyØ4 Geometry Generator - Production Deployment Guide
**Complete Production Deployment Package**  
**Version:** 1.0.0  
**Status:** 🟢 PRODUCTION READY

---

## 🚀 Quick Start

### One-Command Deployment
```bash
# 1. Make scripts executable
chmod +x scripts/*.sh

# 2. Run go-live checklist
./scripts/go_live_checklist.sh

# 3. Deploy to production
./scripts/deploy_production.sh production latest
```

---

## 📋 Complete Deployment Process

### Step 1: Environment Setup

**Create production environment file:**
```bash
cp config/production.env.example config/production.env
```

**Generate secure credentials:**
```bash
# Database password
echo "POSTGRES_PASSWORD=$(openssl rand -hex 32)" >> config/production.env

# JWT secret
echo "JWT_SECRET=$(openssl rand -hex 64)" >> config/production.env

# API key salt
echo "API_KEY_SALT=$(openssl rand -hex 32)" >> config/production.env

# Geometry seed
echo "GEOMETRY_SEED=$(openssl rand -hex 16)" >> config/production.env
```

**Edit config/production.env:**
```env
# Update these values
ALLOWED_ORIGINS=https://your-domain.com
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project

# Verify these are enabled
ETHICS_STRICT_MODE=true
RATE_LIMIT_ENABLED=true
METRICS_ENABLED=true
```

### Step 2: Security Audit

Run the security audit to ensure production readiness:
```bash
./scripts/security_audit.sh
```

Fix any failures before proceeding.

### Step 3: Pre-Deployment Verification

Run the complete verification suite:
```bash
./scripts/verify_complete.sh
```

Expected output:
```
✅ Phase G0 - Geometry Specification
✅ Phase G1 - Prompt Parser
✅ Phase G2 - Ethics Guard
✅ Phase G3 - Temporal System
✅ Phase G4 - Container Integration
✅ Phase G5 - API & Viewer
✅ End-to-end functionality
✅ All required files present
```

### Step 4: Deploy Services

Deploy all services:
```bash
./scripts/deploy_production.sh production latest
```

The script will:
1. Build Docker images
2. Run pre-deployment tests
3. Deploy services (API, DB, Redis, Worker, CDN, Prometheus)
4. Run database migrations
5. Execute smoke tests
6. Display service URLs

### Step 5: Verify Deployment

Run the go-live checklist:
```bash
./scripts/go_live_checklist.sh
```

Expected: All checks pass (green ✅)

### Step 6: Monitor System

Start the monitoring dashboard:
```bash
./scripts/monitoring.sh
```

Or use watch for continuous monitoring:
```bash
watch -n 5 './scripts/monitoring.sh'
```

---

## 🏗️ Architecture

### Service Stack

```
┌─────────────────────────────────────────────────────────┐
│                    Client Layer                         │
│  Web Browser / API Client / Mobile App                 │
└────────────┬────────────────────────────────────────────┘
             │
             ├──► Viewer CDN (nginx:8080)
             │    └─► Static WebGL Viewer
             │
             └──► API Gateway (FastAPI:8000)
                  └─► /geometry/* endpoints
                       │
                       ├──► PostgreSQL (port 5432)
                       │    └─► Geometry tokens, audit logs
                       │
                       ├──► Redis (port 6379)
                       │    └─► Cache, rate limiting
                       │
                       └──► Geometry Worker (Celery)
                            └─► Background tasks
```

### Docker Services

| Service | Image | Ports | Purpose |
|---------|-------|-------|---------|
| `harmony4-api` | harmony4/geometry-api:latest | 8000 | Main API service |
| `geometry-worker` | harmony4/geometry-worker:latest | - | Background task processing |
| `db` | postgres:16-alpine | 5432 | PostgreSQL database |
| `redis` | redis:7-alpine | 6379 | Cache and message broker |
| `viewer-cdn` | nginx:alpine | 8080 | Static file CDN for viewer |
| `prometheus` | prom/prometheus:latest | 9090 | Metrics collection |

---

## 🔐 Security

### Security Features

1. **No Privileged Containers** - All containers run with minimal privileges
2. **Non-Root Users** - Services run as user `harmony` (UID 1000)
3. **Network Isolation** - Services communicate via internal Docker network
4. **Secrets Management** - All secrets in environment variables (not in code)
5. **Ethics Strict Mode** - Hard-coded content blocklists
6. **Rate Limiting** - Prevent abuse (100 req/min default)
7. **Security Headers** - X-Frame-Options, CSP, etc.
8. **HTTPS Ready** - Use reverse proxy (nginx/Caddy) for TLS termination

### Security Checklist

Run before production deployment:
```bash
./scripts/security_audit.sh
```

Checks:
- ✅ No default passwords
- ✅ No hardcoded secrets
- ✅ Secure file permissions
- ✅ No privileged containers
- ✅ No sensitive volume mounts
- ✅ Ethics strict mode enabled
- ✅ Rate limiting configured
- ✅ Security headers present

---

## 📊 Monitoring & Observability

### Health Checks

**API Health:**
```bash
curl http://localhost:8000/geometry/health
```

**Database Health:**
```bash
docker-compose -f docker-compose.geometry.yml exec db pg_isready -U harmony
```

**Redis Health:**
```bash
docker-compose -f docker-compose.geometry.yml exec redis redis-cli ping
```

### Metrics

Access Prometheus metrics:
```bash
open http://localhost:9090
```

Key metrics to monitor:
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- Container resource usage
- Database connections
- Cache hit rate

### Logging

View logs:
```bash
# All services
docker-compose -f docker-compose.geometry.yml logs -f

# Specific service
docker-compose -f docker-compose.geometry.yml logs -f harmony4-api

# Last 100 lines
docker-compose -f docker-compose.geometry.yml logs --tail=100 harmony4-api
```

Logs are stored in:
- Container logs: `docker-compose logs`
- Application logs: `./logs/`

---

## 💾 Backup & Recovery

### Automated Backups

Create a complete system backup:
```bash
./scripts/backup.sh
```

Backups include:
- PostgreSQL database (dump + SQL)
- Redis data
- Configuration files
- Application code
- Geometry containers
- Logs (last 7 days)
- Checksums for verification

Backups are stored in:
```
/backups/harmony4/YYYYMMDD_HHMMSS/
├── database.dump          # PostgreSQL custom dump
├── database.sql           # SQL format
├── redis.rdb              # Redis snapshot
├── config/                # All configuration
├── src/                   # Application code
├── storage/containers/    # Geometry data
├── logs/                  # Application logs
├── checksums.txt          # SHA256 checksums
└── MANIFEST.md            # Backup manifest
```

### Restore from Backup

Restore a complete system backup:
```bash
./scripts/restore.sh /backups/harmony4/20260201_120000
```

The restore process:
1. Stops all services
2. Recreates database
3. Restores database dump
4. Restores configuration
5. Restores geometry containers (optional)
6. Restarts all services
7. Verifies restoration

### Backup Schedule

Set up automated backups with cron:
```bash
# Daily backup at 2 AM
0 2 * * * /path/to/harmony4/scripts/backup.sh

# Weekly cleanup (keep last 4 weeks)
0 3 * * 0 find /backups/harmony4 -type d -mtime +28 -exec rm -rf {} \;
```

---

## 🔧 Operations

### Start Services
```bash
docker-compose -f docker-compose.geometry.yml up -d
```

### Stop Services
```bash
docker-compose -f docker-compose.geometry.yml down
```

### Restart Services
```bash
docker-compose -f docker-compose.geometry.yml restart
```

### Scale Workers
```bash
docker-compose -f docker-compose.geometry.yml up -d --scale geometry-worker=3
```

### Update Deployment
```bash
# Pull latest code
git pull

# Rebuild and deploy
./scripts/deploy_production.sh production latest
```

### View Service Status
```bash
docker-compose -f docker-compose.geometry.yml ps
```

### Execute Commands in Container
```bash
# Python shell
docker-compose -f docker-compose.geometry.yml exec harmony4-api python

# Database shell
docker-compose -f docker-compose.geometry.yml exec db psql -U harmony harmony4

# Redis shell
docker-compose -f docker-compose.geometry.yml exec redis redis-cli
```

---

## 🚨 Troubleshooting

### API Not Responding

1. Check if container is running:
   ```bash
   docker-compose -f docker-compose.geometry.yml ps harmony4-api
   ```

2. Check logs:
   ```bash
   docker-compose -f docker-compose.geometry.yml logs --tail=50 harmony4-api
   ```

3. Restart service:
   ```bash
   docker-compose -f docker-compose.geometry.yml restart harmony4-api
   ```

### Database Connection Issues

1. Verify database is running:
   ```bash
   docker-compose -f docker-compose.geometry.yml exec db pg_isready -U harmony
   ```

2. Check connections:
   ```bash
   docker-compose -f docker-compose.geometry.yml exec db psql -U harmony -c "SELECT count(*) FROM pg_stat_activity;"
   ```

3. Restart database:
   ```bash
   docker-compose -f docker-compose.geometry.yml restart db
   ```

### High Memory Usage

1. Check container stats:
   ```bash
   docker stats
   ```

2. Reduce worker count if needed:
   ```bash
   # Edit docker-compose.geometry.yml
   # Change uvicorn workers from 4 to 2
   ```

3. Clear Redis cache:
   ```bash
   docker-compose -f docker-compose.geometry.yml exec redis redis-cli FLUSHALL
   ```

### Geometry Generation Errors

1. Check ethics validation logs
2. Verify prompt against forbidden patterns
3. Test with simple prompt: "cube"
4. Check worker logs for errors

---

## 📈 Performance Tuning

### Database Optimization

```sql
-- Create indexes for common queries
CREATE INDEX idx_geometry_tokens_uid ON geometry_tokens(uid);
CREATE INDEX idx_geometry_tokens_kind ON geometry_tokens(kind);
CREATE INDEX idx_generation_logs_created_at ON generation_logs(created_at);
```

### Redis Configuration

Adjust Redis memory limits in docker-compose.geometry.yml:
```yaml
command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### API Workers

Adjust worker count based on CPU cores:
```yaml
# In docker-compose.geometry.yml
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "8"]
```

Rule of thumb: `workers = (2 * CPU_cores) + 1`

---

## 🎯 Production Checklist

Before going live:

- [ ] Security audit passed (`./scripts/security_audit.sh`)
- [ ] All verification tests passed (`./scripts/verify_complete.sh`)
- [ ] Go-live checklist passed (`./scripts/go_live_checklist.sh`)
- [ ] Production environment configured (`config/production.env`)
- [ ] Strong passwords generated (32+ chars)
- [ ] SSL/TLS certificates installed
- [ ] Domain DNS configured
- [ ] Firewall rules configured
- [ ] Backup system tested (`./scripts/backup.sh`)
- [ ] Restore tested (`./scripts/restore.sh`)
- [ ] Monitoring dashboard accessible
- [ ] Rate limiting enabled
- [ ] Ethics strict mode enabled
- [ ] Logs configured and rotating
- [ ] Error tracking configured (Sentry)
- [ ] Load testing completed
- [ ] Disaster recovery plan documented
- [ ] Team trained on operations

---

## 🏁 Go Live!

When all checks pass:

```bash
# Final deployment
./scripts/deploy_production.sh production latest

# Start monitoring
./scripts/monitoring.sh

# Celebrate! 🎉
echo "HarmonyØ4 Geometry Generator is LIVE!"
```

---

## 📞 Support

**Documentation:**
- Implementation Guide: [GEOMETRY_IMPLEMENTATION.md](GEOMETRY_IMPLEMENTATION.md)
- Quick Start: [GEOMETRY_QUICK_START.md](GEOMETRY_QUICK_START.md)
- Deployment Manifest: [DEPLOYMENT_MANIFEST.md](DEPLOYMENT_MANIFEST.md)

**API Documentation:**
- Interactive Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/geometry/health

**Scripts:**
- Deploy: `./scripts/deploy_production.sh`
- Verify: `./scripts/verify_complete.sh`
- Monitor: `./scripts/monitoring.sh`
- Backup: `./scripts/backup.sh`
- Restore: `./scripts/restore.sh`
- Security: `./scripts/security_audit.sh`
- Go-Live: `./scripts/go_live_checklist.sh`

---

**Status:** 🟢 **PRODUCTION READY**  
**System:** HarmonyØ4 Ethical Geometry Generator v1.0.0  
**Deployment:** Complete and verified  

🚀 **Ready to change how the world thinks about generative AI!**
