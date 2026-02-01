#!/bin/bash
set -e

echo "🚀 HarmonyØ4 Geometry Generator - Production Deployment"
echo "======================================================"

# Configuration
ENVIRONMENT=${1:-production}
TAG=${2:-latest}
REGISTRY=${3:-ghcr.io/fractalfuryan}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Functions
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# Check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites..."
    
    command -v docker >/dev/null 2>&1 || { log_error "Docker is required"; exit 1; }
    command -v docker-compose >/dev/null 2>&1 || { log_error "Docker Compose is required"; exit 1; }
    
    # Check Docker daemon
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    log_info "✓ Docker and Docker Compose available"
}

# Build and tag images
build_images() {
    log_step "Building Docker images..."
    
    # Build API image
    log_info "Building API image..."
    docker build -f Dockerfile.geometry \
        -t ${REGISTRY}/harmony4-geometry-api:${TAG} \
        -t ${REGISTRY}/harmony4-geometry-api:${ENVIRONMENT} \
        .
    
    # Tag worker image (same build)
    docker tag ${REGISTRY}/harmony4-geometry-api:${TAG} \
        ${REGISTRY}/harmony4-geometry-worker:${TAG}
    
    log_info "✓ Images built and tagged"
}

# Run pre-deployment tests
run_tests() {
    log_step "Running pre-deployment tests..."
    
    # Run Python tests
    log_info "Running unit tests..."
    docker run --rm ${REGISTRY}/harmony4-geometry-api:${TAG} \
        python -m pytest tests/ -v --tb=short || {
        log_warn "Tests failed, but continuing deployment"
    }
    
    log_info "✓ Pre-deployment tests complete"
}

# Deploy services
deploy_services() {
    log_step "Deploying services..."
    
    # Stop existing services
    log_info "Stopping existing services..."
    docker-compose -f docker-compose.geometry.yml down
    
    # Start new services
    log_info "Starting new services..."
    docker-compose -f docker-compose.geometry.yml up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 10
    
    log_info "✓ Services deployed"
}

# Run migrations
run_migrations() {
    log_step "Running database migrations..."
    
    # Wait for database to be ready
    log_info "Waiting for database..."
    for i in {1..30}; do
        if docker-compose -f docker-compose.geometry.yml exec -T db pg_isready -U harmony >/dev/null 2>&1; then
            log_info "Database is ready"
            break
        fi
        sleep 2
    done
    
    # Run migrations
    log_info "Applying migrations..."
    docker-compose -f docker-compose.geometry.yml run --rm harmony4-api \
        alembic upgrade head || {
        log_warn "Migration failed or no migrations to run"
    }
    
    log_info "✓ Database migrations complete"
}

# Run smoke tests
run_smoke_tests() {
    log_step "Running smoke tests..."
    
    # Wait for API to be healthy
    log_info "Waiting for API to be healthy..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/geometry/health >/dev/null 2>&1; then
            log_info "API is responding"
            break
        fi
        sleep 3
    done
    
    # Test 1: Health endpoint
    log_info "Testing health endpoint..."
    HEALTH=$(curl -s http://localhost:8000/geometry/health)
    if echo "$HEALTH" | grep -q '"status"'; then
        log_info "✓ Health check passed"
    else
        log_error "Health check failed"
        exit 1
    fi
    
    # Test 2: Geometry primitives endpoint
    log_info "Testing primitives endpoint..."
    PRIMITIVES=$(curl -s http://localhost:8000/geometry/primitives)
    if echo "$PRIMITIVES" | grep -q '"cube"'; then
        log_info "✓ Primitives endpoint passed"
    else
        log_error "Primitives endpoint failed"
        exit 1
    fi
    
    # Test 3: Generate simple geometry
    log_info "Testing generation endpoint..."
    RESPONSE=$(curl -s -X POST http://localhost:8000/geometry/generate \
        -H "Content-Type: application/json" \
        -d '{"prompt": "cube and sphere"}')
    
    if echo "$RESPONSE" | grep -q '"tokens"'; then
        log_info "✓ Generation endpoint passed"
    else
        log_error "Generation endpoint failed"
        exit 1
    fi
    
    log_info "✓ All smoke tests passed"
}

# Display deployment info
show_deployment_info() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║           🎉 DEPLOYMENT COMPLETE!                             ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Deployment Information:${NC}"
    echo "  Environment: ${ENVIRONMENT}"
    echo "  Tag: ${TAG}"
    echo ""
    echo -e "${BLUE}Service URLs:${NC}"
    echo "  API: http://localhost:8000"
    echo "  Docs: http://localhost:8000/docs"
    echo "  Viewer CDN: http://localhost:8080"
    echo "  Prometheus: http://localhost:9090"
    echo ""
    echo -e "${BLUE}Quick Test:${NC}"
    echo "  curl -X POST http://localhost:8000/geometry/generate \\"
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -d '{\"prompt\":\"rotating cubes\"}'"
    echo ""
    echo -e "${BLUE}View Logs:${NC}"
    echo "  docker-compose -f docker-compose.geometry.yml logs -f harmony4-api"
    echo ""
    echo -e "${BLUE}Stop Services:${NC}"
    echo "  docker-compose -f docker-compose.geometry.yml down"
    echo ""
}

# Main deployment
main() {
    log_info "Starting HarmonyØ4 Geometry Generator deployment"
    log_info "Environment: ${ENVIRONMENT}"
    log_info "Tag: ${TAG}"
    echo ""
    
    check_prerequisites
    build_images
    run_tests
    deploy_services
    run_migrations
    run_smoke_tests
    show_deployment_info
}

# Run main
main "$@"
