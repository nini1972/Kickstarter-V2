"""
🔐 Authentication Models
Future-proof user authentication with modern security practices
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import uuid
import re

# User Roles Enum for RBAC
class UserRole(str, Enum):
    ADMIN = "admin"
    PREMIUM = "premium"
    USER = "user"
    READONLY = "readonly"

# User Status Enum
class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"

# Core User Model
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=200)
    hashed_password: str
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.PENDING_VERIFICATION
    is_verified: bool = False
    
    # Profile Information
    avatar_url: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = None
    
    # Investment Preferences
    preferred_categories: List[str] = Field(default_factory=list)
    risk_tolerance: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    investment_budget: Optional[float] = Field(None, ge=0)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    email_verified_at: Optional[datetime] = None
    
    # Security
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    password_changed_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.lower()
    
    @validator('website')
    def validate_website(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            v = f'https://{v}'
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# User Registration Request
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=200)
    
    @validator('password')
    def validate_password(cls, v):
        # Modern password requirements
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

# User Login Request
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False

# User Response (for API responses)
class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str]
    role: UserRole
    status: UserStatus
    is_verified: bool
    avatar_url: Optional[str]
    bio: Optional[str]
    location: Optional[str]
    website: Optional[str]
    preferred_categories: List[str]
    risk_tolerance: Optional[str]
    investment_budget: Optional[float]
    created_at: datetime
    last_login: Optional[datetime]

# User Update Request
class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=200)
    bio: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = None
    preferred_categories: Optional[List[str]] = None
    risk_tolerance: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    investment_budget: Optional[float] = Field(None, ge=0)
    avatar_url: Optional[str] = None

# Password Change Request
class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        # Same validation as UserCreate
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

# Password Reset Request
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        # Same validation as UserCreate
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

# JWT Token Models
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserResponse

class TokenRefresh(BaseModel):
    refresh_token: str

class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
    token_type: Optional[str] = None  # access or refresh
    exp: Optional[int] = None

# Session Management
class UserSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    refresh_token: str
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    last_used: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

# Email Verification
class EmailVerification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    email: str
    token: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    is_used: bool = False

# Two-Factor Authentication (Future Enhancement)
class TwoFactorAuth(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    secret_key: str
    backup_codes: List[str] = Field(default_factory=list)
    is_enabled: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

# API Key Management (For Premium Users)
class APIKey(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str = Field(..., min_length=1, max_length=100)
    key_hash: str
    permissions: List[str] = Field(default_factory=list)
    rate_limit: int = 1000  # requests per hour
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True

# User Activity Log
class UserActivity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    action: str = Field(..., max_length=100)
    resource: Optional[str] = Field(None, max_length=100)
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Optional[dict] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Role-Based Access Control
class Permission(BaseModel):
    name: str
    description: str
    resource: str
    action: str

class RolePermissions(BaseModel):
    role: UserRole
    permissions: List[Permission]

# Default Permissions Configuration
DEFAULT_PERMISSIONS = {
    UserRole.ADMIN: [
        "users:create", "users:read", "users:update", "users:delete",
        "projects:create", "projects:read", "projects:update", "projects:delete",
        "investments:create", "investments:read", "investments:update", "investments:delete",
        "analytics:read", "alerts:read", "alerts:update", "system:manage"
    ],
    UserRole.PREMIUM: [
        "projects:create", "projects:read", "projects:update", "projects:delete",
        "investments:create", "investments:read", "investments:update", "investments:delete",
        "analytics:read", "alerts:read", "alerts:update", "ai:advanced"
    ],
    UserRole.USER: [
        "projects:create", "projects:read", "projects:update",
        "investments:create", "investments:read", "investments:update",
        "analytics:read", "alerts:read"
    ],
    UserRole.READONLY: [
        "projects:read", "investments:read", "analytics:read", "alerts:read"
    ]
}