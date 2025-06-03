#!/bin/bash

# 🚀 Backend Production Deployment Script for AWS Lightsail
# Automated deployment for Kickstarter Investment Tracker Backend

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Configuration
BACKEND_DIR="/app/backend"
DEPLOY_DIR="/app/kickstarter"
COMPOSE_FILE="docker/docker-compose.production.yml"

# Server setup check
check_server_setup() {
    log_info "🔍 Checking server setup..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        echo "Run: curl -fsSL https://get.docker.com | sh"
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        echo "Run: sudo curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)\" -o /usr/local/bin/docker-compose"
        echo "Then: sudo chmod +x /usr/local/bin/docker-compose"
        exit 1
    fi
    
    # Check if user can run Docker
    if ! docker ps &> /dev/null; then
        log_error "Cannot run Docker commands. Please add user to docker group:"
        echo "sudo usermod -aG docker $USER"
        echo "Then log out and log back in."
        exit 1
    fi
    
    log_success "Server setup check passed"
}

# Environment validation
validate_environment() {
    log_info "⚙️ Validating production environment..."
    
    if [[ ! -f "$BACKEND_DIR/.env.production" ]]; then
        log_error "Production environment file not found: $BACKEND_DIR/.env.production"
        log_info "Please create .env.production with required variables:"
        echo "- MONGO_URL (MongoDB Atlas connection string)"
        echo "- OPENAI_API_KEY (your production OpenAI key)"
        echo "- JWT_SECRET_KEY (64+ character secure secret)"
        echo "- CORS_ORIGINS (your frontend domains)"
        exit 1
    fi
    
    # Source environment file
    source "$BACKEND_DIR/.env.production"
    
    # Check required variables
    required_vars=("MONGO_URL" "OPENAI_API_KEY" "JWT_SECRET_KEY" "CORS_ORIGINS")
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "Missing required environment variables: ${missing_vars[*]}"
        exit 1
    fi
    
    # Validate JWT secret length
    if [[ ${#JWT_SECRET_KEY} -lt 64 ]]; then
        log_error "JWT_SECRET_KEY must be at least 64 characters long"
        exit 1
    fi
    
    log_success "Environment validation passed"
}

# Prepare deployment directory
prepare_deployment() {
    log_info "📁 Preparing deployment directory..."
    
    # Create deployment directory if it doesn't exist
    sudo mkdir -p "$DEPLOY_DIR"
    sudo chown $USER:$USER "$DEPLOY_DIR"
    
    # Copy backend files to deployment directory
    log_info "📋 Copying backend files..."
    cp -r "$BACKEND_DIR"/* "$DEPLOY_DIR/"
    
    # Ensure .env.production is copied
    cp "$BACKEND_DIR/.env.production" "$DEPLOY_DIR/.env.production"
    
    # Create required directories
    mkdir -p "$DEPLOY_DIR/logs/nginx"
    mkdir -p "$DEPLOY_DIR/backups"
    mkdir -p "$DEPLOY_DIR/ssl"
    mkdir -p "$DEPLOY_DIR/grafana/dashboards"
    mkdir -p "$DEPLOY_DIR/grafana/datasources"
    
    # Set proper permissions
    chmod 755 "$DEPLOY_DIR/logs" "$DEPLOY_DIR/backups"
    chmod 700 "$DEPLOY_DIR/ssl"
    
    log_success "Deployment directory prepared"
}

# Deploy services
deploy_services() {
    log_info "🚀 Deploying production services..."
    
    cd "$DEPLOY_DIR"
    
    # Stop any existing services
    log_info "🛑 Stopping existing services..."
    docker-compose -f "$COMPOSE_FILE" down --timeout 30 || true
    
    # Pull latest images
    log_info "📥 Pulling latest Docker images..."
    docker-compose -f "$COMPOSE_FILE" pull
    
    # Build application image
    log_info "🏗️ Building application image..."
    docker-compose -f "$COMPOSE_FILE" build --no-cache backend
    
    # Start services
    log_info "▶️ Starting production services..."
    docker-compose -f "$COMPOSE_FILE" up -d
    
    log_success "Services deployed"
}

# Wait for services to be healthy
wait_for_health() {
    log_info "⏳ Waiting for services to become healthy..."
    
    max_wait=300  # 5 minutes
    wait_time=0
    
    while [[ $wait_time -lt $max_wait ]]; do
        # Check backend health
        if curl -f -s http://localhost:8001/api/health > /dev/null; then
            log_success "✅ Backend service is healthy"
            break
        fi
        
        log_info "⏳ Waiting for backend service... (${wait_time}s elapsed)"
        sleep 10
        wait_time=$((wait_time + 10))
    done
    
    if [[ $wait_time -ge $max_wait ]]; then
        log_error "❌ Health check timeout after ${max_wait}s"
        return 1
    fi
    
    # Additional service checks
    log_info "🔍 Checking individual services..."
    
    # Check Redis
    if docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping | grep -q PONG; then
        log_success "✅ Redis service is healthy"
    else
        log_warning "⚠️ Redis health check failed"
    fi
    
    # Check if using local MongoDB
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q mongodb; then
        if docker-compose -f "$COMPOSE_FILE" exec -T mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
            log_success "✅ MongoDB service is healthy"
        else
            log_warning "⚠️ MongoDB health check failed"
        fi
    fi
    
    log_success "All services are running"
}

# Verify deployment
verify_deployment() {
    log_info "🔍 Verifying deployment..."
    
    # Test API endpoints
    endpoints=(
        "/api/health"
        "/api/metrics"
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
        log_success "✅ Database connectivity verified"
    else
        log_error "❌ Database connectivity failed: $db_health"
        return 1
    fi
    
    # Test cache connectivity
    log_info "Testing cache connectivity..."
    cache_health=$(curl -s http://localhost:8001/api/health | jq -r '.services.redis.status // "unknown"')
    
    if [[ "$cache_health" == "healthy" ]]; then
        log_success "✅ Cache connectivity verified"
    else
        log_warning "⚠️ Cache connectivity failed: $cache_health"
    fi
    
    log_success "Deployment verification completed"
}

# Setup firewall
setup_firewall() {
    log_info "🔥 Configuring firewall..."
    
    # Check if ufw is installed
    if command -v ufw &> /dev/null; then
        # Configure firewall rules
        sudo ufw allow ssh
        sudo ufw allow 80/tcp
        sudo ufw allow 443/tcp
        sudo ufw allow 8001/tcp
        sudo ufw allow 9090/tcp  # Prometheus (restrict this in production)
        sudo ufw allow 3001/tcp  # Grafana (restrict this in production)
        
        # Enable firewall
        echo "y" | sudo ufw enable || true
        
        log_success "✅ Firewall configured"
        log_warning "⚠️ Consider restricting monitoring ports (9090, 3001) to specific IPs"
    else
        log_warning "⚠️ UFW not installed. Please configure firewall manually."
    fi
}

# Generate deployment report
generate_report() {
    log_info "📊 Generating deployment report..."
    
    # Get server info
    SERVER_IP=$(curl -s http://checkip.amazonaws.com/ || echo "Unknown")
    
    # Get service status
    SERVICES_STATUS=$(docker-compose -f "$COMPOSE_FILE" ps --format "table {{.Service}}\t{{.Status}}")
    
    # Generate report
    cat > "$DEPLOY_DIR/deployment-report.txt" << EOF
🚀 Backend Deployment Report
Generated: $(date)

Server Information:
- Server IP: $SERVER_IP
- Deployment Directory: $DEPLOY_DIR
- Environment: production

Service URLs:
- Backend API: http://$SERVER_IP:8001
- Health Check: http://$SERVER_IP:8001/api/health
- Metrics: http://$SERVER_IP:8001/api/metrics
- Prometheus: http://$SERVER_IP:9090
- Grafana: http://$SERVER_IP:3001

Services Status:
$SERVICES_STATUS

Verification Checklist:
[ ] All services running
[ ] Health checks passing
[ ] Database connectivity verified
[ ] Cache connectivity verified
[ ] API endpoints responding
[ ] Monitoring accessible
[ ] Firewall configured

Next Steps:
1. Update frontend CORS_ORIGINS to include your backend URL
2. Configure custom domain and SSL (optional)
3. Set up monitoring alerts
4. Test complete application flow
5. Configure backup schedule

Security Notes:
- Restrict monitoring ports to admin IPs only
- Set up SSL certificates for HTTPS
- Monitor security logs regularly
- Update dependencies regularly
EOF

    log_success "Deployment report saved to $DEPLOY_DIR/deployment-report.txt"
}

# Cleanup function
cleanup() {
    log_info "🧹 Cleaning up Docker resources..."
    
    # Remove dangling images
    docker image prune -f
    
    # Remove unused containers
    docker container prune -f
    
    log_success "Cleanup completed"
}

# Main deployment function
main() {
    log_info "🚀 Starting backend production deployment"
    log_info "Target server: $(hostname -I | awk '{print $1}')"
    
    # Deployment steps
    check_server_setup
    validate_environment
    prepare_deployment
    deploy_services
    
    if wait_for_health; then
        if verify_deployment; then
            setup_firewall
            generate_report
            cleanup
            
            log_success "🎉 Backend deployment completed successfully!"
            
            # Display deployment summary
            echo ""
            log_info "📊 Deployment Summary:"
            log_info "Backend API: http://$(curl -s http://checkip.amazonaws.com/):8001"
            log_info "Health Check: http://$(curl -s http://checkip.amazonaws.com/):8001/api/health"
            log_info "Prometheus: http://$(curl -s http://checkip.amazonaws.com/):9090"
            log_info "Grafana: http://$(curl -s http://checkip.amazonaws.com/):3001"
            echo ""
            log_warning "⚠️ Important: Update frontend CORS_ORIGINS to include your backend URL"
            log_info "Check deployment-report.txt for detailed information"
            
        else
            log_error "❌ Deployment verification failed"
            log_info "Check logs: docker-compose -f $COMPOSE_FILE logs"
            exit 1
        fi
    else
        log_error "❌ Services failed to become healthy"
        log_info "Check logs: docker-compose -f $COMPOSE_FILE logs"
        exit 1
    fi
}

# Handle script interruption
trap 'log_error "Deployment interrupted"; exit 1' INT TERM

# Run main function
main "$@"
