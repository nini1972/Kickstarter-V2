"""
🔐 JWT Security Services
Modern, future-proof authentication utilities with enhanced security
"""

import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets
import string
from passlib.context import CryptContext
from models.auth import TokenData, UserRole, User
import logging

logger = logging.getLogger(__name__)

class AuthConfig:
    """Centralized authentication configuration"""
    SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-super-secret-jwt-key-change-this-in-production-min-32-chars')
    ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '30'))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRE_DAYS', '7'))
    RESET_TOKEN_EXPIRE_HOURS = int(os.environ.get('JWT_RESET_TOKEN_EXPIRE_HOURS', '1'))
    BCRYPT_ROUNDS = int(os.environ.get('BCRYPT_ROUNDS', '12'))
    SECURE_COOKIES = os.environ.get('SECURE_COOKIES', 'False').lower() == 'true'
    COOKIE_DOMAIN = os.environ.get('COOKIE_DOMAIN', 'localhost')

class SecurityService:
    """Advanced security service with modern practices"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.security = HTTPBearer(auto_error=False)
    
    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt and configurable rounds"""
        salt = bcrypt.gensalt(rounds=AuthConfig.BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure random token"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def generate_backup_codes(self, count: int = 10) -> list:
        """Generate backup codes for 2FA"""
        return [self.generate_secure_token(8) for _ in range(count)]

class JWTService:
    """Modern JWT service with enhanced security features"""
    
    def __init__(self):
        self.config = AuthConfig()
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token with configurable expiration"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.config.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.config.SECRET_KEY, algorithm=self.config.ALGORITHM)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Failed to create access token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create access token"
            )
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token with longer expiration"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.config.REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.config.SECRET_KEY, algorithm=self.config.ALGORITHM)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Failed to create refresh token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create refresh token"
            )
    
    def create_reset_token(self, email: str) -> str:
        """Create password reset token"""
        to_encode = {
            "email": email,
            "type": "reset",
            "exp": datetime.utcnow() + timedelta(hours=self.config.RESET_TOKEN_EXPIRE_HOURS),
            "iat": datetime.utcnow()
        }
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.config.SECRET_KEY, algorithm=self.config.ALGORITHM)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Failed to create reset token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create reset token"
            )
    
    def verify_token(self, token: str, token_type: str = "access") -> TokenData:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.config.SECRET_KEY, algorithms=[self.config.ALGORITHM])
            
            # Verify token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type}"
                )
            
            # Extract user data
            user_id: str = payload.get("sub")
            email: str = payload.get("email")
            role: str = payload.get("role")
            exp: int = payload.get("exp")
            
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            return TokenData(
                user_id=user_id,
                email=email,
                role=UserRole(role) if role else None,
                token_type=token_type,
                exp=exp
            )
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token verification failed"
            )
    
    def decode_reset_token(self, token: str) -> str:
        """Decode password reset token and return email"""
        try:
            payload = jwt.decode(token, self.config.SECRET_KEY, algorithms=[self.config.ALGORITHM])
            
            if payload.get("type") != "reset":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid reset token type"
                )
            
            email: str = payload.get("email")
            if email is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid reset token payload"
                )
            
            return email
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )

class AuthDependency:
    """Authentication dependencies for FastAPI routes"""
    
    def __init__(self):
        self.jwt_service = JWTService()
        self.security = HTTPBearer(auto_error=False)
    
    async def get_current_user_optional(
        self, 
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
    ) -> Optional[TokenData]:
        """Get current user from token (optional - returns None if no token)"""
        # Try to get token from cookies first (secure method)
        access_token = request.cookies.get("access_token")
        
        # Fallback to Authorization header for backward compatibility
        if not access_token and credentials:
            access_token = credentials.credentials
        
        if not access_token:
            return None
        
        try:
            token_data = self.jwt_service.verify_token(access_token, "access")
            return token_data
        except HTTPException:
            return None
    
    async def get_current_user(
        self, 
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
    ) -> TokenData:
        """Get current user from token (required) - supports both cookies and Authorization header"""
        try:
            # Try to get token from cookies first (secure method)
            access_token = request.cookies.get("access_token")
            
            # Fallback to Authorization header for backward compatibility
            if not access_token and credentials:
                access_token = credentials.credentials
            
            if not access_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated - no token provided",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            token_data = self.jwt_service.verify_token(access_token, "access")
            
            # Log authentication attempt
            auth_method = "cookie" if request.cookies.get("access_token") else "header"
            logger.info(f"User authenticated via {auth_method}: {token_data.user_id} from IP: {request.client.host}")
            
            return token_data
        except HTTPException as e:
            logger.warning(f"Authentication failed from IP: {request.client.host} - {e.detail}")
            raise e
    
    def require_role(self, allowed_roles: list[UserRole]):
        """Decorator to require specific roles"""
        async def role_checker(
            current_user: TokenData = Depends(self.get_current_user)
        ) -> TokenData:
            if current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {[role.value for role in allowed_roles]}"
                )
            return current_user
        return role_checker
    
    def require_permission(self, permission: str):
        """Decorator to require specific permission"""
        async def permission_checker(
            current_user: TokenData = Depends(self.get_current_user)
        ) -> TokenData:
            from models.auth import DEFAULT_PERMISSIONS
            
            user_permissions = DEFAULT_PERMISSIONS.get(current_user.role, [])
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required permission: {permission}"
                )
            return current_user
        return permission_checker

class RateLimitService:
    """Enhanced rate limiting for authentication endpoints"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
    
    async def check_login_attempts(self, identifier: str, max_attempts: int = 5) -> bool:
        """Check if login attempts exceed limit"""
        if not self.redis_client:
            return True  # Allow if Redis not available
        
        try:
            key = f"login_attempts:{identifier}"
            attempts = await self.redis_client.get(key)
            
            if attempts and int(attempts) >= max_attempts:
                return False
            
            return True
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True  # Allow if check fails
    
    async def record_failed_login(self, identifier: str, lockout_minutes: int = 15):
        """Record failed login attempt"""
        if not self.redis_client:
            return
        
        try:
            key = f"login_attempts:{identifier}"
            await self.redis_client.incr(key)
            await self.redis_client.expire(key, lockout_minutes * 60)
        except Exception as e:
            logger.error(f"Failed to record login attempt: {e}")
    
    async def clear_login_attempts(self, identifier: str):
        """Clear login attempts after successful login"""
        if not self.redis_client:
            return
        
        try:
            key = f"login_attempts:{identifier}"
            await self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Failed to clear login attempts: {e}")

# Global instances
security_service = SecurityService()
jwt_service = JWTService()
auth_dependency = AuthDependency()

# FastAPI Dependencies
get_current_user = auth_dependency.get_current_user
get_current_user_optional = auth_dependency.get_current_user_optional
require_role = auth_dependency.require_role
require_permission = auth_dependency.require_permission

# Role-based dependencies
require_admin = require_role([UserRole.ADMIN])
require_premium = require_role([UserRole.PREMIUM, UserRole.ADMIN])
require_user = require_role([UserRole.USER, UserRole.PREMIUM, UserRole.ADMIN])