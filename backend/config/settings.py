"""
⚙️ Application Configuration
Centralized configuration management for production readiness
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

class DatabaseConfig:
    """Database configuration settings"""
    MONGO_URL: str = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/kickstarter_tracker')
    DB_NAME: Optional[str] = None  # Extracted from MONGO_URL
    
    @classmethod
    def get_db_name(cls) -> str:
        """Extract database name from MONGO_URL"""
        if cls.DB_NAME is None:
            url_parts = cls.MONGO_URL.split('/')
            cls.DB_NAME = url_parts[-1] if len(url_parts) > 3 else 'kickstarter_tracker'
        return cls.DB_NAME

class RedisConfig:
    """Redis cache configuration"""
    REDIS_URL: str = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    CACHE_TTL: int = int(os.environ.get('CACHE_TTL', '3600'))  # 1 hour default

class OpenAIConfig:
    """OpenAI API configuration"""
    API_KEY: str = os.environ.get('OPENAI_API_KEY', 'sk-placeholder-key')
    MODEL: str = os.environ.get('OPENAI_MODEL', 'gpt-4')
    MAX_TOKENS: int = int(os.environ.get('OPENAI_MAX_TOKENS', '1000'))
    TEMPERATURE: float = float(os.environ.get('OPENAI_TEMPERATURE', '0.7'))
    TIMEOUT: int = int(os.environ.get('OPENAI_TIMEOUT', '30'))
    MAX_RETRIES: int = int(os.environ.get('OPENAI_MAX_RETRIES', '3'))

class AuthConfig:
    """JWT Authentication configuration"""
    # SECURITY: JWT_SECRET_KEY is required and MUST be set via environment variable
    # No default value provided to prevent accidental use of weak secrets
    SECRET_KEY: str = os.environ.get('JWT_SECRET_KEY')
    ALGORITHM: str = os.environ.get('JWT_ALGORITHM', 'HS256')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '30'))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRE_DAYS', '7'))
    RESET_TOKEN_EXPIRE_HOURS: int = int(os.environ.get('JWT_RESET_TOKEN_EXPIRE_HOURS', '1'))
    BCRYPT_ROUNDS: int = int(os.environ.get('BCRYPT_ROUNDS', '12'))
    SECURE_COOKIES: bool = os.environ.get('SECURE_COOKIES', 'False').lower() == 'true'
    
    # Minimum required length for JWT secret key (industry standard)
    MIN_SECRET_KEY_LENGTH: int = 32
    COOKIE_DOMAIN: str = os.environ.get('COOKIE_DOMAIN', 'localhost')

class ServerConfig:
    """Server configuration settings"""
    HOST: str = os.environ.get('HOST', '0.0.0.0')
    PORT: int = int(os.environ.get('PORT', '8001'))
    DEBUG: bool = os.environ.get('DEBUG', 'False').lower() == 'true'
    RELOAD: bool = os.environ.get('RELOAD', 'False').lower() == 'true'
    
    # CORS settings
    CORS_ORIGINS: list = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000').split(',')
    CORS_METHODS: list = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    CORS_HEADERS: list = ["*"]

class RateLimitConfig:
    """Rate limiting configuration"""
    HEALTH_CHECK_LIMIT: str = os.environ.get('RATE_LIMIT_HEALTH', '30/minute')
    API_LIMIT: str = os.environ.get('RATE_LIMIT_API', '100/minute')
    AUTH_LIMIT: str = os.environ.get('RATE_LIMIT_AUTH', '5/minute')
    BATCH_LIMIT: str = os.environ.get('RATE_LIMIT_BATCH', '10/hour')
    UPLOAD_LIMIT: str = os.environ.get('RATE_LIMIT_UPLOAD', '20/hour')

class LoggingConfig:
    """Logging configuration"""
    LEVEL: str = os.environ.get('LOG_LEVEL', 'INFO')
    FORMAT: str = os.environ.get('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    FILE_PATH: Optional[str] = os.environ.get('LOG_FILE_PATH')
    MAX_BYTES: int = int(os.environ.get('LOG_MAX_BYTES', '10485760'))  # 10MB
    BACKUP_COUNT: int = int(os.environ.get('LOG_BACKUP_COUNT', '5'))

class AppConfig:
    """Main application configuration"""
    TITLE: str = "Kickstarter Investment Tracker"
    DESCRIPTION: str = "AI-powered investment tracking and analysis platform"
    VERSION: str = "2.0.0"
    
    # Feature flags
    ENABLE_AI_ANALYSIS: bool = os.environ.get('ENABLE_AI_ANALYSIS', 'True').lower() == 'true'
    ENABLE_BATCH_PROCESSING: bool = os.environ.get('ENABLE_BATCH_PROCESSING', 'True').lower() == 'true'
    ENABLE_CACHING: bool = os.environ.get('ENABLE_CACHING', 'True').lower() == 'true'
    ENABLE_RATE_LIMITING: bool = os.environ.get('ENABLE_RATE_LIMITING', 'True').lower() == 'true'
    
    # Performance settings
    MAX_PROJECTS_LIMIT: int = int(os.environ.get('MAX_PROJECTS_LIMIT', '1000'))
    DEFAULT_PAGE_SIZE: int = int(os.environ.get('DEFAULT_PAGE_SIZE', '50'))
    BATCH_SIZE_LIMIT: int = int(os.environ.get('BATCH_SIZE_LIMIT', '10'))

# Global configuration instances
db_config = DatabaseConfig()
redis_config = RedisConfig()
openai_config = OpenAIConfig()
auth_config = AuthConfig()
server_config = ServerConfig()
rate_limit_config = RateLimitConfig()
logging_config = LoggingConfig()
app_config = AppConfig()

# Validation
def validate_config():
    """Validate critical configuration settings with enhanced security checks"""
    required_vars = {
        'MONGO_URL': db_config.MONGO_URL,
        'OPENAI_API_KEY': openai_config.API_KEY,
        'JWT_SECRET_KEY': auth_config.SECRET_KEY
    }
    
    missing_vars = []
    security_issues = []
    
    for var_name, var_value in required_vars.items():
        if not var_value:
            missing_vars.append(var_name)
        elif var_value.startswith('sk-placeholder') or 'change-this' in var_value:
            missing_vars.append(var_name)
    
    # Enhanced JWT Secret Key Security Validation
    jwt_secret = auth_config.SECRET_KEY
    if jwt_secret:
        if len(jwt_secret) < auth_config.MIN_SECRET_KEY_LENGTH:
            security_issues.append(f"JWT_SECRET_KEY too short (minimum {auth_config.MIN_SECRET_KEY_LENGTH} characters)")
        
        # Check for weak/common patterns
        weak_patterns = ['secret', 'password', '123', 'abc', 'test', 'dev']
        if any(pattern in jwt_secret.lower() for pattern in weak_patterns):
            security_issues.append("JWT_SECRET_KEY contains weak/common patterns")
    else:
        # Critical: No JWT secret at all
        missing_vars.append('JWT_SECRET_KEY (CRITICAL - Authentication will fail)')
    
    # Report issues
    if missing_vars:
        print(f"🚨 CRITICAL: Missing or placeholder values for: {', '.join(missing_vars)}")
        print("🔧 Please update these in your .env file immediately!")
    
    if security_issues:
        print(f"⚠️  SECURITY WARNING: {', '.join(security_issues)}")
        print("🔐 Please generate a strong, random JWT secret key")
    
    if not missing_vars and not security_issues:
        print("✅ Configuration validation passed")
    
    return len(missing_vars) == 0 and len(security_issues) == 0

# Auto-validate on import
if __name__ != "__main__":
    validate_config()