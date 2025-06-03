#!/bin/bash

# 🍃 MongoDB Atlas Setup Guide Script
# Interactive setup for MongoDB Atlas production database

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

# Interactive MongoDB Atlas setup
setup_mongodb_atlas() {
    log_info "🍃 MongoDB Atlas Setup for Kickstarter Investment Tracker"
    echo ""
    
    echo "This script will guide you through setting up MongoDB Atlas for production."
    echo ""
    
    # Step 1: Account creation
    log_info "📝 Step 1: Create MongoDB Atlas Account"
    echo "1. Go to https://cloud.mongodb.com"
    echo "2. Click 'Try Free' or 'Sign In' if you have an account"
    echo "3. Create account with your email"
    echo ""
    read -p "Press Enter when you have created your account and are logged in..."
    
    # Step 2: Organization and Project
    log_info "🏢 Step 2: Create Organization and Project"
    echo "1. If this is your first time, MongoDB will prompt you to create an organization"
    echo "2. Organization name: 'Your Company' or 'Personal Projects'"
    echo "3. Create a new project named: 'Kickstarter Investment Tracker'"
    echo ""
    read -p "Press Enter when you have created the project..."
    
    # Step 3: Cluster creation
    log_info "🖥️ Step 3: Create Database Cluster"
    echo "1. Click 'Create a New Cluster' or 'Build a Database'"
    echo "2. Choose deployment type:"
    echo "   - For development/testing: M0 Sandbox (FREE)"
    echo "   - For production: M2 or M5 (paid, better performance)"
    echo "3. Choose cloud provider: AWS (recommended)"
    echo "4. Choose region closest to your users"
    echo "5. Cluster name: 'kickstarter-prod'"
    echo "6. Click 'Create Cluster'"
    echo ""
    read -p "Press Enter when your cluster is being created (it takes 3-7 minutes)..."
    
    # Step 4: Database user
    log_info "👤 Step 4: Create Database User"
    echo "1. In the sidebar, click 'Database Access'"
    echo "2. Click 'Add New Database User'"
    echo "3. Authentication Method: Password"
    echo "4. Username: 'prod-user'"
    echo "5. Password: Generate a secure password (save it!)"
    echo "6. Database User Privileges: 'Read and write to any database'"
    echo "7. Click 'Add User'"
    echo ""
    
    read -p "Enter the username you created: " DB_USERNAME
    read -p "Enter the password you created: " -s DB_PASSWORD
    echo ""
    
    # Step 5: Network access
    log_info "🌐 Step 5: Configure Network Access"
    echo "1. In the sidebar, click 'Network Access'"
    echo "2. Click 'Add IP Address'"
    echo "3. For testing: Click 'Allow Access from Anywhere' (0.0.0.0/0)"
    echo "4. For production: Add your server's specific IP address"
    echo "5. Comment: 'Production Server'"
    echo "6. Click 'Confirm'"
    echo ""
    log_warning "⚠️ Important: In production, only allow specific IP addresses!"
    echo ""
    read -p "Press Enter when you have configured network access..."
    
    # Step 6: Get connection string
    log_info "🔗 Step 6: Get Connection String"
    echo "1. Go back to 'Database' in the sidebar"
    echo "2. Your cluster should be ready (green status)"
    echo "3. Click 'Connect' button"
    echo "4. Choose 'Connect your application'"
    echo "5. Driver: Node.js, Version: 4.1 or later"
    echo "6. Copy the connection string"
    echo ""
    
    read -p "Paste your connection string here: " CONNECTION_STRING
    
    # Step 7: Process connection string
    log_info "⚙️ Step 7: Processing Connection String"
    
    # Replace placeholders in connection string
    PROCESSED_CONNECTION_STRING=$(echo "$CONNECTION_STRING" | sed "s/<username>/$DB_USERNAME/g" | sed "s/<password>/$DB_PASSWORD/g")
    
    # Add database name if not present
    if [[ "$PROCESSED_CONNECTION_STRING" != *"/kickstarter_prod?"* ]]; then
        PROCESSED_CONNECTION_STRING=$(echo "$PROCESSED_CONNECTION_STRING" | sed 's|mongodb+srv://[^/]*/|&kickstarter_prod|')
    fi
    
    log_success "✅ Connection string processed"
    
    # Step 8: Test connection
    log_info "🧪 Step 8: Test Connection (Optional)"
    echo "You can test the connection using MongoDB Compass or mongosh:"
    echo ""
    echo "Connection String:"
    echo "$PROCESSED_CONNECTION_STRING"
    echo ""
    
    # Step 9: Generate environment configuration
    log_info "📝 Step 9: Generate Environment Configuration"
    
    cat > mongodb-atlas-config.txt << EOF
# 🍃 MongoDB Atlas Configuration
# Generated: $(date)

# Database Connection Details
MONGO_URL=$PROCESSED_CONNECTION_STRING
MONGODB_USERNAME=$DB_USERNAME
MONGODB_PASSWORD=$DB_PASSWORD
MONGODB_DATABASE=kickstarter_prod

# Cluster Information
MONGODB_CLUSTER=$(echo "$CONNECTION_STRING" | grep -o '@[^/]*' | sed 's/@//')

# Usage Instructions:
# 1. Copy the MONGO_URL to your .env.production file
# 2. Make sure your server IP is whitelisted in MongoDB Atlas
# 3. Test the connection before deploying

# Security Notes:
# - Never commit these credentials to version control
# - Use environment variables in production
# - Regularly rotate passwords
# - Restrict network access to specific IPs in production
EOF

    log_success "✅ Configuration saved to mongodb-atlas-config.txt"
    
    # Step 10: Security recommendations
    log_warning "🔒 Security Recommendations:"
    echo ""
    echo "1. 🔐 Database Security:"
    echo "   - Use strong, unique passwords"
    echo "   - Enable database auditing"
    echo "   - Restrict network access to specific IPs"
    echo ""
    echo "2. 🔄 Backup Configuration:"
    echo "   - MongoDB Atlas provides automatic backups"
    echo "   - Configure backup retention period"
    echo "   - Test backup restoration procedures"
    echo ""
    echo "3. 📊 Monitoring:"
    echo "   - Enable MongoDB Atlas monitoring"
    echo "   - Set up alerts for performance issues"
    echo "   - Monitor database connections and performance"
    echo ""
    
    # Step 11: Next steps
    log_info "🎯 Next Steps:"
    echo ""
    echo "1. Copy MONGO_URL from mongodb-atlas-config.txt to your .env.production file"
    echo "2. Deploy your backend with the new database configuration"
    echo "3. Test all database operations"
    echo "4. Set up monitoring and alerts"
    echo "5. Configure backup notifications"
    echo ""
    
    log_success "🎉 MongoDB Atlas setup completed!"
    log_info "Your database is ready for production use."
}

# Verify MongoDB Atlas setup
verify_setup() {
    log_info "🔍 Verifying MongoDB Atlas Setup"
    
    if [[ ! -f "mongodb-atlas-config.txt" ]]; then
        log_error "❌ Configuration file not found. Please run the setup first."
        exit 1
    fi
    
    # Source the configuration
    source mongodb-atlas-config.txt
    
    if [[ -z "$MONGO_URL" ]]; then
        log_error "❌ MONGO_URL not found in configuration"
        exit 1
    fi
    
    log_success "✅ Configuration file found"
    
    # Test connection using mongosh (if available)
    if command -v mongosh &> /dev/null; then
        log_info "🧪 Testing database connection..."
        
        if timeout 10 mongosh "$MONGO_URL" --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
            log_success "✅ Database connection successful"
        else
            log_warning "⚠️ Database connection test failed. Please check:"
            echo "  - Network access is configured correctly"
            echo "  - Username and password are correct"
            echo "  - Your IP address is whitelisted"
        fi
    else
        log_warning "⚠️ mongosh not installed. Skipping connection test."
        log_info "Install mongosh to test connections: https://docs.mongodb.com/mongodb-shell/install/"
    fi
    
    log_info "📋 Configuration Summary:"
    echo "  - Database: kickstarter_prod"
    echo "  - Username: $MONGODB_USERNAME"
    echo "  - Cluster: $MONGODB_CLUSTER"
    echo "  - Connection configured: ✅"
}

# Main function
main() {
    echo "🍃 MongoDB Atlas Setup for Kickstarter Investment Tracker"
    echo "============================================================"
    echo ""
    
    case "${1:-setup}" in
        "setup")
            setup_mongodb_atlas
            ;;
        "verify")
            verify_setup
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [setup|verify|help]"
            echo ""
            echo "Commands:"
            echo "  setup   - Interactive MongoDB Atlas setup (default)"
            echo "  verify  - Verify existing configuration"
            echo "  help    - Show this help message"
            ;;
        *)
            log_error "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
