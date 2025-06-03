"""
🏭 Production Configuration
Enterprise-grade production settings for MongoDB Atlas deployment
"""

import os
import logging
from typing import Dict, Any, Optional
from urllib.parse import quote_plus
import ssl
from pathlib import Path

class ProductionDatabaseConfig:
    """MongoDB Atlas production configuration with security and performance optimizations"""
    
    def __init__(self):
        self.environment = os.environ.get('ENVIRONMENT', 'development')
        self.is_production = self.environment == 'production'
        
    def get_mongodb_atlas_connection_string(self) -> str:
        """
        Generate secure MongoDB Atlas connection string with production optimizations
        
        Returns:
            Optimized connection string for MongoDB Atlas
        """
        if not self.is_production:
            return os.environ.get('MONGO_URL', 'mongodb://localhost:27017/kickstarter_tracker')
        
        # Production MongoDB Atlas configuration
        username = os.environ.get('MONGODB_USERNAME')
        password = os.environ.get('MONGODB_PASSWORD') 
        cluster = os.environ.get('MONGODB_CLUSTER', 'cluster0.mongodb.net')
        database = os.environ.get('MONGODB_DATABASE', 'kickstarter_prod')
        
        if not username or not password:
            raise ValueError("Production MongoDB credentials not configured")
        
        # URL encode credentials to handle special characters
        encoded_username = quote_plus(username)
        encoded_password = quote_plus(password)
        
        # Production-optimized connection string
        connection_string = (
            f"mongodb+srv://{encoded_username}:{encoded_password}@{cluster}/{database}"
            f"?retryWrites=true"
            f"&w=majority"
            f"&readPreference=primary"
            f"&connectTimeoutMS=10000"
            f"&socketTimeoutMS=45000"
            f"&maxPoolSize=50"
            f"&minPoolSize=5"
            f"&maxIdleTimeMS=300000"
            f"&ssl=true"
            f"&authSource=admin"
        )
        
        return connection_string
    
    def get_mongodb_client_options(self) -> Dict[str, Any]:
        """
        Get MongoDB client options optimized for production
        
        Returns:
            Dictionary of client options
        """
        if not self.is_production:
            return {}
        
        return {
            # Connection pool settings
            "maxPoolSize": 50,
            "minPoolSize": 5,
            "maxIdleTimeMS": 300000,
            "waitQueueTimeoutMS": 10000,
            
            # Timeout settings
            "connectTimeoutMS": 10000,
            "socketTimeoutMS": 45000,
            "serverSelectionTimeoutMS": 10000,
            
            # SSL/TLS settings
            "ssl": True,
            "ssl_cert_reqs": ssl.CERT_REQUIRED,
            
            # Write concern
            "w": "majority",
            "wtimeoutMS": 10000,
            
            # Read preference
            "readPreference": "primary",
            
            # Retry writes
            "retryWrites": True,
            
            # Application name for monitoring
            "appName": "KickstarterInvestmentTracker"
        }

class ProductionSecurityConfig:
    """Production security configuration with enhanced protection"""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """
        Get production security headers
        
        Returns:
            Dictionary of security headers
        """
        return {
            # Content Security Policy
            "Content-Security-Policy": os.environ.get(
                'CONTENT_SECURITY_POLICY',
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://vercel.live; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' https://api.openai.com;"
            ),
            
            # Security headers
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            
            # HSTS (HTTP Strict Transport Security)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            
            # Feature Policy
            "Feature-Policy": "geolocation 'none'; microphone 'none'; camera 'none'",
        }
    
    @staticmethod
    def get_cors_config() -> Dict[str, Any]:
        """
        Get production CORS configuration
        
        Returns:
            CORS configuration dictionary
        """
        return {
            "allow_origins": os.environ.get(
                'CORS_ORIGINS', 
                'https://your-app.vercel.app'
            ).split(','),
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": [
                "Authorization",
                "Content-Type",
                "X-Requested-With",
                "Accept",
                "Origin"
            ],
            "expose_headers": [
                "X-Total-Count",
                "X-Page-Count"
            ]
        }

class ProductionMonitoringConfig:
    """Production monitoring and observability configuration"""
    
    @staticmethod
    def setup_logging() -> None:
        """Setup production logging configuration"""
        log_level = os.environ.get('LOG_LEVEL', 'INFO')
        log_file = os.environ.get('LOG_FILE_PATH', '/var/log/kickstarter/app.log')
        
        # Create log directory if it doesn't exist
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        # Set specific loggers
        logging.getLogger('uvicorn').setLevel(logging.INFO)
        logging.getLogger('motor').setLevel(logging.WARNING)
        logging.getLogger('pymongo').setLevel(logging.WARNING)
    
    @staticmethod
    def get_health_check_config() -> Dict[str, Any]:
        """
        Get health check configuration
        
        Returns:
            Health check configuration
        """
        return {
            "timeout": int(os.environ.get('HEALTH_CHECK_TIMEOUT', '30')),
            "interval": int(os.environ.get('HEALTH_CHECK_INTERVAL', '60')),
            "retries": int(os.environ.get('HEALTH_CHECK_RETRIES', '3')),
            "start_period": int(os.environ.get('HEALTH_CHECK_START_PERIOD', '60'))
        }

class ProductionBackupConfig:
    """Production backup and disaster recovery configuration"""
    
    @staticmethod
    def get_backup_strategy() -> Dict[str, Any]:
        """
        Get production backup strategy configuration
        
        Returns:
            Backup configuration dictionary
        """
        return {
            # MongoDB Atlas automatic backups
            "mongodb_atlas_backup": {
                "enabled": True,
                "retention_days": 7,
                "point_in_time_recovery": True,
                "backup_frequency": "continuous"
            },
            
            # Application-level backup settings
            "application_backup": {
                "enabled": os.environ.get('BACKUP_ENABLED', 'true').lower() == 'true',
                "schedule": os.environ.get('BACKUP_SCHEDULE', '0 2 * * *'),  # Daily at 2 AM
                "retention_days": int(os.environ.get('BACKUP_RETENTION_DAYS', '30')),
                "compression": True,
                "encryption": True
            },
            
            # Disaster recovery settings
            "disaster_recovery": {
                "rto_minutes": 30,  # Recovery Time Objective
                "rpo_minutes": 15,  # Recovery Point Objective
                "backup_regions": ["us-east-1", "eu-west-1"],
                "automated_failover": True
            }
        }

class ProductionPerformanceConfig:
    """Production performance optimization configuration"""
    
    @staticmethod
    def get_caching_strategy() -> Dict[str, Any]:
        """
        Get production caching strategy
        
        Returns:
            Caching configuration dictionary
        """
        return {
            # Redis configuration
            "redis": {
                "url": os.environ.get('REDIS_URL', 'redis://localhost:6379'),
                "max_connections": int(os.environ.get('REDIS_MAX_CONNECTIONS', '50')),
                "socket_timeout": int(os.environ.get('REDIS_SOCKET_TIMEOUT', '5')),
                "socket_connect_timeout": int(os.environ.get('REDIS_CONNECT_TIMEOUT', '5')),
                "retry_on_timeout": True,
                "health_check_interval": 30
            },
            
            # Cache TTL settings (in seconds)
            "ttl": {
                "analytics_dashboard": 1800,  # 30 minutes
                "market_insights": 3600,      # 1 hour
                "user_profile": 900,          # 15 minutes
                "project_list": 600,          # 10 minutes
                "health_check": 60            # 1 minute
            },
            
            # Cache invalidation strategy
            "invalidation": {
                "strategy": "time_based",
                "background_refresh": True,
                "stale_while_revalidate": True
            }
        }

# Global production configuration instances
production_db_config = ProductionDatabaseConfig()
production_security_config = ProductionSecurityConfig()
production_monitoring_config = ProductionMonitoringConfig()
production_backup_config = ProductionBackupConfig()
production_performance_config = ProductionPerformanceConfig()

def validate_production_config() -> bool:
    """
    Validate production configuration completeness
    
    Returns:
        True if configuration is valid for production
    """
    required_env_vars = [
        'MONGODB_USERNAME',
        'MONGODB_PASSWORD', 
        'MONGODB_CLUSTER',
        'JWT_SECRET_KEY',
        'OPENAI_API_KEY',
        'CORS_ORIGINS'
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        logging.error(f"❌ Missing production environment variables: {missing_vars}")
        return False
    
    # Validate JWT secret strength
    jwt_secret = os.environ.get('JWT_SECRET_KEY', '')
    if len(jwt_secret) < 64:
        logging.error("❌ JWT_SECRET_KEY must be at least 64 characters for production")
        return False
    
    logging.info("✅ Production configuration validated successfully")
    return True
