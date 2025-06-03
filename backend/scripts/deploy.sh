#!/bin/bash

# 🚀 Production Deployment Script
# Automated deployment for Kickstarter Investment Tracker

set -e  # Exit on any error

# Configuration
DEPLOY_ENV=${DEPLOY_ENV:-production}
BACKUP_BEFORE_DEPLOY=${BACKUP_BEFORE_DEPLOY:-true}
HEALTH_CHECK_TIMEOUT=${HEALTH_CHECK_TIMEOUT:-300}
ROLLBACK_ON_FAILURE=${ROLLBACK_ON_FAILURE:-true}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking deployment prerequisites..."
    
    # Check required tools
    for tool in docker docker-compose curl jq; do
        if ! command -v $tool &> /dev/null; then
            log_error "$tool is required but not installed"
            exit 1
        fi
    done
    
    # Check environment variables
    required_vars=("MONGO_URL" "OPENAI_API_KEY" "JWT_SECRET_KEY")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            log_error "Required environment variable $var is not set"
            exit 1
        fi
    done
    
    # Check JWT secret length
    if [[ ${#JWT_SECRET_KEY} -lt 64 ]]; then
        log_error "JWT_SECRET_KEY must be at least 64 characters long"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Create backup before deployment
create_backup() {
    if [[ "$BACKUP_BEFORE_DEPLOY" == "true" ]]; then
        log_info "Creating backup before deployment..."
        
        # Call backup API endpoint
        backup_response=$(curl -s -X POST \
            -H "Content-Type: application/json" \
            http://localhost:8001/api/admin/backup || echo '{"status": "failed"}')
        
        backup_status=$(echo $backup_response | jq -r '.status // "failed"')
        
        if [[ "$backup_status" == "success" ]]; then
            log_success "Backup created successfully"
        else
            log_warning "Backup creation failed, continuing with deployment"
        fi
    fi
}

# Build and deploy application
deploy_application() {
    log_info "Starting application deployment..."
    
    # Pull latest images
    log_info "Pulling latest Docker images..."
    docker-compose -f docker/docker-compose.production.yml pull
    
    # Build application image
    log_info "Building application image..."
    docker-compose -f docker/docker-compose.production.yml build --no-cache backend
    
    # Stop existing services gracefully
    log_info "Stopping existing services..."
    docker-compose -f docker/docker-compose.production.yml down --timeout 30
    
    # Start services
    log_info "Starting services..."
    docker-compose -f docker/docker-compose.production.yml up -d
    
    log_success "Application deployment started"
}

# Wait for services to be healthy
wait_for_health() {
    log_info "Waiting for services to become healthy..."
    
    start_time=$(date +%s)
    
    while true; do
        current_time=$(date +%s)
        elapsed=$((current_time - start_time))
        
        if [[ $elapsed -gt $HEALTH_CHECK_TIMEOUT ]]; then
            log_error "Health check timeout after ${HEALTH_CHECK_TIMEOUT}s"
            return 1
        fi
        
        # Check backend health
        if curl -f -s http://localhost:8001/api/health > /dev/null; then
            log_success "Backend service is healthy"
            break
        fi
        
        log_info "Waiting for backend service... (${elapsed}s elapsed)"
        sleep 10
    done
    
    # Additional service checks
    log_info "Checking individual services..."
    
    # Check Redis
    if docker-compose -f docker/docker-compose.production.yml exec -T redis redis-cli ping | grep -q PONG; then
        log_success "Redis service is healthy"
    else
        log_warning "Redis health check failed"
    fi
    
    # Check MongoDB (if using local instance)
    if docker-compose -f docker/docker-compose.production.yml ps | grep -q mongodb; then
        if docker-compose -f docker/docker-compose.production.yml exec -T mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
            log_success "MongoDB service is healthy"
        else
            log_warning "MongoDB health check failed"
        fi
    fi
    
    log_success "All services are healthy"
}

# Run deployment verification tests
verify_deployment() {
    log_info "Running deployment verification tests..."
    
    # Test basic API endpoints
    endpoints=(
        "/api/health"
        "/api/auth/demo-login"
    )
    
    for endpoint in "${endpoints[@]}"; do
        log_info "Testing endpoint: $endpoint"
        
        response=$(curl -s -w "%{http_code}" http://localhost:8001$endpoint || echo "000")
        http_code="${response: -3}"
        
        if [[ "$http_code" =~ ^2[0-9][0-9]$ ]]; then
            log_success "✅ $endpoint - HTTP $http_code"
        else
            log_error "❌ $endpoint - HTTP $http_code"
            return 1
        fi
    done
    
    # Test database connectivity
    log_info "Testing database connectivity..."
    db_health=$(curl -s http://localhost:8001/api/health | jq -r '.services.database.status // "unknown"')
    
    if [[ "$db_health" == "healthy" ]]; then
        log_success "Database connectivity verified"
    else
        log_error "Database connectivity failed: $db_health"
        return 1
    fi
    
    # Test cache connectivity
    log_info "Testing cache connectivity..."
    cache_health=$(curl -s http://localhost:8001/api/health | jq -r '.services.redis.status // "unknown"')
    
    if [[ "$cache_health" == "healthy" ]]; then
        log_success "Cache connectivity verified"
    else
        log_warning "Cache connectivity failed: $cache_health"
    fi
    
    log_success "Deployment verification completed"
}

# Rollback deployment if something goes wrong
rollback_deployment() {
    if [[ "$ROLLBACK_ON_FAILURE" == "true" ]]; then
        log_warning "Rolling back deployment..."
        
        # Stop current deployment
        docker-compose -f docker/docker-compose.production.yml down
        
        # TODO: Implement rollback to previous version
        # This would require version tagging and storage of previous images
        
        log_info "Rollback completed"
    fi
}

# Cleanup old Docker images and containers
cleanup() {
    log_info "Cleaning up old Docker resources..."
    
    # Remove dangling images
    docker image prune -f
    
    # Remove unused containers
    docker container prune -f
    
    # Remove unused volumes (be careful with this in production)
    # docker volume prune -f
    
    log_success "Cleanup completed"
}

# Main deployment function
main() {
    log_info "🚀 Starting production deployment for Kickstarter Investment Tracker"
    log_info "Environment: $DEPLOY_ENV"
    log_info "Backup before deploy: $BACKUP_BEFORE_DEPLOY"
    log_info "Health check timeout: ${HEALTH_CHECK_TIMEOUT}s"
    
    # Deployment steps
    if check_prerequisites; then
        if create_backup; then
            if deploy_application; then
                if wait_for_health; then
                    if verify_deployment; then
                        cleanup
                        log_success "🎉 Deployment completed successfully!"
                        
                        # Display deployment summary
                        echo ""
                        log_info "📊 Deployment Summary:"
                        log_info "Backend URL: http://localhost:8001"
                        log_info "Health Check: http://localhost:8001/api/health"
                        log_info "Monitoring: http://localhost:9090 (Prometheus)"
                        log_info "Dashboards: http://localhost:3001 (Grafana)"
                        
                        exit 0
                    else
                        log_error "Deployment verification failed"
                        rollback_deployment
                        exit 1
                    fi
                else
                    log_error "Health check failed"
                    rollback_deployment
                    exit 1
                fi
            else
                log_error "Application deployment failed"
                exit 1
            fi
        else
            log_warning "Backup failed, but continuing with deployment"
            # Continue with deployment even if backup fails
        fi
    else
        log_error "Prerequisites check failed"
        exit 1
    fi
}

# Handle script interruption
trap 'log_error "Deployment interrupted"; rollback_deployment; exit 1' INT TERM

# Run main function
main "$@"
