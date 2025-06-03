#!/bin/bash

# 🏭 Production Environment Setup Script
# Automated setup for production deployment

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

# Function to generate secure random string
generate_secret() {
    local length=${1:-64}
    openssl rand -base64 $length | tr -d "=+/" | cut -c1-$length
}

# Create production environment file
create_production_env() {
    log_info "Creating production environment configuration..."
    
    if [[ -f .env.production ]]; then
        log_warning ".env.production already exists. Creating backup..."
        cp .env.production .env.production.backup.$(date +%Y%m%d_%H%M%S)
    fi
    
    # Generate secure JWT secret
    JWT_SECRET=$(generate_secret 64)
    
    # Create production environment file
    cat > .env.production << EOF
# 🏭 PRODUCTION ENVIRONMENT CONFIGURATION
# Generated on $(date)

# MongoDB Configuration (MongoDB Atlas)
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/kickstarter_prod?retryWrites=true&w=majority
MONGODB_USERNAME=your-mongodb-username
MONGODB_PASSWORD=your-mongodb-password
MONGODB_CLUSTER=cluster0.mongodb.net
MONGODB_DATABASE=kickstarter_prod

# Redis Configuration
REDIS_URL=redis://redis:6379
REDIS_PASSWORD=$(generate_secret 32)

# OpenAI API Configuration
OPENAI_API_KEY=your-production-openai-api-key-here

# JWT Security Configuration
JWT_SECRET_KEY=$JWT_SECRET
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Production Security
BCRYPT_ROUNDS=14
SECURE_COOKIES=true
COOKIE_DOMAIN=your-production-domain.com
ENVIRONMENT=production

# Server Configuration
HOST=0.0.0.0
PORT=8001
DEBUG=false

# CORS Configuration
CORS_ORIGINS=https://your-frontend.vercel.app,https://your-custom-domain.com

# Production Rate Limits
RATE_LIMIT_API=200/minute
RATE_LIMIT_AUTH=10/minute
RATE_LIMIT_LOGIN=3/minute
RATE_LIMIT_REGISTRATION=2/minute

# Monitoring & Backup
BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=30
LOG_LEVEL=INFO

# AWS S3 Backup (optional)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
BACKUP_S3_BUCKET=your-backup-bucket
BACKUP_S3_REGION=us-east-1

# Grafana
GRAFANA_PASSWORD=$(generate_secret 16)
EOF
    
    log_success "Production environment file created"
    log_warning "IMPORTANT: Please update the following values in .env.production:"
    echo "  - MONGO_URL (MongoDB Atlas connection string)"
    echo "  - MONGODB_USERNAME, MONGODB_PASSWORD, MONGODB_CLUSTER"
    echo "  - OPENAI_API_KEY (your production OpenAI API key)"
    echo "  - COOKIE_DOMAIN (your production domain)"
    echo "  - CORS_ORIGINS (your frontend URLs)"
    echo "  - AWS credentials (if using S3 backup)"
}

# Setup MongoDB Atlas connection
setup_mongodb_atlas() {
    log_info "MongoDB Atlas setup instructions:"
    echo ""
    echo "1. Go to https://cloud.mongodb.com"
    echo "2. Create a new cluster or use existing one"
    echo "3. Create a database user with read/write permissions"
    echo "4. Whitelist your server IP addresses"
    echo "5. Get the connection string and update MONGO_URL in .env.production"
    echo ""
    log_warning "Don't forget to replace <username>, <password>, and <cluster> in the connection string"
}

# Setup directory structure
setup_directories() {
    log_info "Creating production directory structure..."
    
    # Create required directories
    mkdir -p logs/nginx
    mkdir -p backups
    mkdir -p ssl
    mkdir -p grafana/{dashboards,datasources}
    mkdir -p docker
    
    # Set proper permissions
    chmod 755 logs backups
    chmod 700 ssl
    
    log_success "Directory structure created"
}

# Setup SSL certificates (Let's Encrypt)
setup_ssl() {
    log_info "SSL certificate setup instructions:"
    echo ""
    echo "For production deployment, you'll need SSL certificates:"
    echo ""
    echo "Option 1: Let's Encrypt (recommended)"
    echo "  sudo apt-get install certbot"
    echo "  sudo certbot certonly --standalone -d your-domain.com"
    echo "  sudo cp /etc/letsencrypt/live/your-domain.com/*.pem ssl/"
    echo ""
    echo "Option 2: Custom certificates"
    echo "  Copy your certificate files to the ssl/ directory:"
    echo "  - ssl/cert.pem (certificate)"
    echo "  - ssl/key.pem (private key)"
    echo ""
    log_warning "Update nginx.conf to enable HTTPS when certificates are ready"
}

# Setup monitoring
setup_monitoring() {
    log_info "Setting up monitoring configuration..."
    
    # Create Grafana datasource configuration
    cat > grafana/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

    # Create basic dashboard configuration
    cat > grafana/dashboards/dashboard.yml << EOF
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF

    log_success "Monitoring configuration created"
}

# Setup backup configuration
setup_backup() {
    log_info "Setting up backup configuration..."
    
    # Create backup script
    cat > scripts/backup.sh << 'EOF'
#!/bin/bash
# Automated backup script

set -e

log_info() {
    echo "[$(date)] INFO: $1"
}

log_error() {
    echo "[$(date)] ERROR: $1"
}

# Trigger backup via API
backup_response=$(curl -s -X POST \
    -H "Authorization: Bearer $ADMIN_API_KEY" \
    http://localhost:8001/api/admin/backup)

backup_status=$(echo $backup_response | jq -r '.status // "failed"')

if [[ "$backup_status" == "success" ]]; then
    log_info "Backup completed successfully"
    exit 0
else
    log_error "Backup failed: $backup_response"
    exit 1
fi
EOF

    chmod +x scripts/backup.sh
    
    log_success "Backup configuration created"
    log_info "To schedule automatic backups, add to crontab:"
    echo "  0 2 * * * /path/to/scripts/backup.sh >> /var/log/backup.log 2>&1"
}

# Setup firewall rules
setup_firewall() {
    log_info "Firewall setup instructions:"
    echo ""
    echo "Configure firewall rules for production:"
    echo ""
    echo "sudo ufw allow ssh"
    echo "sudo ufw allow 80/tcp   # HTTP"
    echo "sudo ufw allow 443/tcp  # HTTPS"
    echo "sudo ufw allow 9090/tcp # Prometheus (restrict to monitoring IPs)"
    echo "sudo ufw allow 3001/tcp # Grafana (restrict to admin IPs)"
    echo "sudo ufw --force enable"
    echo ""
    log_warning "Restrict monitoring ports (9090, 3001) to specific IP addresses"
}

# Verify production setup
verify_setup() {
    log_info "Verifying production setup..."
    
    # Check required files
    required_files=(
        ".env.production"
        "docker/Dockerfile.production"
        "docker/docker-compose.production.yml"
        "docker/nginx.conf"
        "scripts/deploy.sh"
    )
    
    for file in "${required_files[@]}"; do
        if [[ -f "$file" ]]; then
            log_success "✅ $file exists"
        else
            log_error "❌ $file missing"
        fi
    done
    
    # Check directories
    required_dirs=("logs" "backups" "ssl" "grafana")
    
    for dir in "${required_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            log_success "✅ Directory $dir exists"
        else
            log_error "❌ Directory $dir missing"
        fi
    done
    
    # Check environment variables
    if [[ -f ".env.production" ]]; then
        source .env.production
        
        if [[ ${#JWT_SECRET_KEY} -ge 64 ]]; then
            log_success "✅ JWT secret key is secure"
        else
            log_error "❌ JWT secret key too short"
        fi
        
        if [[ "$SECURE_COOKIES" == "true" ]]; then
            log_success "✅ Secure cookies enabled"
        else
            log_warning "⚠️ Secure cookies should be enabled for production"
        fi
    fi
    
    log_success "Production setup verification completed"
}

# Main setup function
main() {
    log_info "🏭 Setting up production environment for Kickstarter Investment Tracker"
    
    echo ""
    log_info "This script will:"
    echo "  1. Create production environment configuration"
    echo "  2. Setup directory structure"
    echo "  3. Configure monitoring"
    echo "  4. Setup backup system"
    echo "  5. Provide SSL and firewall instructions"
    echo ""
    
    read -p "Continue with production setup? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        create_production_env
        setup_directories
        setup_monitoring
        setup_backup
        verify_setup
        
        echo ""
        log_success "🎉 Production setup completed!"
        echo ""
        log_info "Next steps:"
        echo "  1. Update .env.production with your actual credentials"
        echo "  2. Setup MongoDB Atlas database"
        echo "  3. Configure SSL certificates"
        echo "  4. Setup firewall rules"
        echo "  5. Run deployment: ./scripts/deploy.sh"
        echo ""
        
        setup_mongodb_atlas
        setup_ssl
        setup_firewall
        
    else
        log_info "Production setup cancelled"
    fi
}

# Run main function
main "$@"
