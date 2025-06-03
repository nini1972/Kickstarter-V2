#!/bin/bash

# 🚀 Frontend Production Deployment Script
# Automated Vercel deployment for Kickstarter Investment Tracker

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
FRONTEND_DIR="/app/frontend"
BACKEND_URL=${BACKEND_URL:-""}
ENVIRONMENT=${ENVIRONMENT:-"production"}

# Check if we're in the right directory
if [[ ! -f "$FRONTEND_DIR/package.json" ]]; then
    log_error "Frontend directory not found. Please run from project root."
    exit 1
fi

log_info "🚀 Starting frontend production deployment"

# Step 1: Install dependencies
log_info "📦 Installing dependencies..."
cd $FRONTEND_DIR
npm install --production=false

# Step 2: Configure environment
log_info "⚙️ Configuring production environment..."

if [[ -z "$BACKEND_URL" ]]; then
    log_warning "BACKEND_URL not provided. Please set it manually in Vercel dashboard."
    BACKEND_URL="https://your-backend-domain.com"
fi

# Create or update .env.production
cat > .env.production << EOF
# Production Environment Configuration
REACT_APP_BACKEND_URL=$BACKEND_URL
REACT_APP_ENVIRONMENT=production
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENABLE_AI_INSIGHTS=true
REACT_APP_ENABLE_DEVTOOLS=false
REACT_APP_API_TIMEOUT=30000
REACT_APP_CACHE_TTL=300000
EOF

log_success "Production environment configured"

# Step 3: Build production bundle
log_info "🏗️ Building production bundle..."
npm run build

if [[ $? -eq 0 ]]; then
    log_success "Production build completed successfully"
else
    log_error "Production build failed"
    exit 1
fi

# Step 4: Check build output
log_info "📊 Analyzing build output..."
BUILD_SIZE=$(du -sh build/ | cut -f1)
log_info "Build size: $BUILD_SIZE"

# Check for common issues
if [[ ! -f "build/index.html" ]]; then
    log_error "Build output missing index.html"
    exit 1
fi

if [[ ! -d "build/static" ]]; then
    log_error "Build output missing static assets"
    exit 1
fi

log_success "Build output validated"

# Step 5: Deploy to Vercel
log_info "🚀 Deploying to Vercel..."

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    log_warning "Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Check if already linked to Vercel project
if [[ ! -f ".vercel/project.json" ]]; then
    log_info "Linking to Vercel project..."
    vercel link --yes
fi

# Deploy to production
log_info "Deploying to production..."
VERCEL_OUTPUT=$(vercel --prod --yes 2>&1)
DEPLOY_EXIT_CODE=$?

if [[ $DEPLOY_EXIT_CODE -eq 0 ]]; then
    # Extract deployment URL
    DEPLOYMENT_URL=$(echo "$VERCEL_OUTPUT" | grep -E "https://.*\.vercel\.app" | tail -1 | awk '{print $NF}')
    
    log_success "🎉 Frontend deployed successfully!"
    log_info "Deployment URL: $DEPLOYMENT_URL"
    
    # Save deployment info
    echo "$DEPLOYMENT_URL" > .vercel/last-deployment.txt
    date >> .vercel/last-deployment.txt
    
else
    log_error "Vercel deployment failed"
    log_error "$VERCEL_OUTPUT"
    exit 1
fi

# Step 6: Verify deployment
log_info "🔍 Verifying deployment..."

# Test if deployment is accessible
if curl -f -s "$DEPLOYMENT_URL" > /dev/null; then
    log_success "✅ Deployment is accessible"
else
    log_warning "⚠️ Deployment may not be ready yet. Please check manually."
fi

# Step 7: Post-deployment instructions
log_info "📋 Post-deployment checklist:"
echo ""
echo "✅ Frontend deployed to: $DEPLOYMENT_URL"
echo "✅ Environment: $ENVIRONMENT"
echo "✅ Backend URL configured: $BACKEND_URL"
echo ""
log_warning "⚠️ Important next steps:"
echo "1. Update CORS settings in backend to include: $DEPLOYMENT_URL"
echo "2. Test authentication and all features"
echo "3. Configure custom domain (optional)"
echo "4. Set up monitoring and error tracking"
echo ""

# Step 8: Generate verification report
log_info "📊 Generating deployment report..."

cat > deployment-report.txt << EOF
🚀 Frontend Deployment Report
Generated: $(date)

Deployment Details:
- Environment: $ENVIRONMENT
- Frontend URL: $DEPLOYMENT_URL
- Backend URL: $BACKEND_URL
- Build Size: $BUILD_SIZE
- Deployment Time: $(date)

Verification Checklist:
[ ] Frontend loads successfully
[ ] Authentication works
[ ] API calls to backend work
[ ] All features functional
[ ] Performance acceptable
[ ] Security headers present

Next Steps:
1. Update backend CORS settings
2. Test complete application flow
3. Configure custom domain (optional)
4. Monitor application performance
EOF

log_success "Deployment report saved to deployment-report.txt"

# Step 9: Open deployment in browser (if possible)
if command -v open &> /dev/null; then
    log_info "🌐 Opening deployment in browser..."
    open "$DEPLOYMENT_URL"
elif command -v xdg-open &> /dev/null; then
    log_info "🌐 Opening deployment in browser..."
    xdg-open "$DEPLOYMENT_URL"
else
    log_info "🌐 Open this URL in your browser: $DEPLOYMENT_URL"
fi

log_success "🎉 Frontend deployment completed successfully!"
log_info "Your Kickstarter Investment Tracker frontend is now live!"

exit 0
