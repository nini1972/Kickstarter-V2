"""
🔐 Authentication Routes
Future-proof authentication endpoints with comprehensive security
"""

from fastapi import APIRouter, HTTPException, status, Depends, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from datetime import datetime, timedelta
from typing import Optional
import logging

# Database imports
from motor.motor_asyncio import AsyncIOMotorClient
import os

# Local imports
from models.auth import (
    UserCreate, UserLogin, UserResponse, Token, TokenRefresh, 
    PasswordChange, PasswordResetRequest, PasswordReset,
    User, UserRole, UserStatus, UserSession
)
from services.auth import (
    security_service, jwt_service, get_current_user, 
    get_current_user_optional, RateLimitService
)

logger = logging.getLogger(__name__)

# Router
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

# Database connection (will be injected)
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/kickstarter_tracker')
client = AsyncIOMotorClient(mongo_url)
db = client.get_database()

# Rate limiting
rate_limiter = RateLimitService()

@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, request: Request):
    """Register a new user with comprehensive validation"""
    try:
        # Check if user already exists
        existing_user = await db.users.find_one({
            "$or": [
                {"email": user_data.email.lower()},
                {"username": user_data.username.lower()}
            ]
        })
        
        if existing_user:
            if existing_user.get("email") == user_data.email.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        # Hash password
        hashed_password = security_service.hash_password(user_data.password)
        
        # Create user
        user = User(
            email=user_data.email.lower(),
            username=user_data.username.lower(),
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            role=UserRole.USER,
            status=UserStatus.PENDING_VERIFICATION
        )
        
        # Save to database
        user_dict = user.model_dump()
        result = await db.users.insert_one(user_dict)
        
        if not result.inserted_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
        
        # Log registration
        logger.info(f"New user registered: {user.email} from IP: {request.client.host}")
        
        # Return user response (excluding sensitive data)
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            status=user.status,
            is_verified=user.is_verified,
            avatar_url=user.avatar_url,
            bio=user.bio,
            location=user.location,
            website=user.website,
            preferred_categories=user.preferred_categories,
            risk_tolerance=user.risk_tolerance,
            investment_budget=user.investment_budget,
            created_at=user.created_at,
            last_login=user.last_login
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@auth_router.post("/login", response_model=Token)
async def login_user(user_credentials: UserLogin, request: Request, response: Response):
    """Authenticate user and return JWT tokens"""
    try:
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "Unknown")
        
        # Rate limiting check
        if not await rate_limiter.check_login_attempts(user_credentials.email):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Please try again later."
            )
        
        # Find user
        user_data = await db.users.find_one({"email": user_credentials.email.lower()})
        
        if not user_data:
            await rate_limiter.record_failed_login(user_credentials.email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        user = User(**user_data)
        
        # Check if user is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked. Please try again later."
            )
        
        # Verify password
        if not security_service.verify_password(user_credentials.password, user.hashed_password):
            # Record failed attempt
            await rate_limiter.record_failed_login(user_credentials.email)
            
            # Update failed login attempts
            failed_attempts = user.failed_login_attempts + 1
            update_data = {"failed_login_attempts": failed_attempts}
            
            # Lock account after 5 failed attempts
            if failed_attempts >= 5:
                lock_until = datetime.utcnow() + timedelta(minutes=30)
                update_data["locked_until"] = lock_until
                logger.warning(f"Account locked for user {user.email} due to failed attempts")
            
            await db.users.update_one(
                {"id": user.id},
                {"$set": update_data}
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check user status
        if user.status == UserStatus.SUSPENDED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is suspended"
            )
        
        if user.status == UserStatus.INACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )
        
        # Clear failed login attempts
        await rate_limiter.clear_login_attempts(user_credentials.email)
        
        # Create tokens
        token_data = {
            "sub": user.id,
            "email": user.email,
            "role": user.role.value,
            "username": user.username
        }
        
        access_token = jwt_service.create_access_token(token_data)
        refresh_token = jwt_service.create_refresh_token({"sub": user.id, "email": user.email})
        
        # Calculate expiration time
        expires_in = jwt_service.config.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        
        # Create session record
        session = UserSession(
            user_id=user.id,
            refresh_token=refresh_token,
            device_info=f"{user_agent}",
            ip_address=client_ip,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(days=jwt_service.config.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        
        # Save session
        await db.user_sessions.insert_one(session.model_dump())
        
        # Update user last login and clear failed attempts
        await db.users.update_one(
            {"id": user.id},
            {
                "$set": {
                    "last_login": datetime.utcnow(),
                    "failed_login_attempts": 0,
                    "locked_until": None
                }
            }
        )
        
        # Set secure HTTP-only cookies for both access and refresh tokens
        # This replaces localStorage storage to prevent XSS attacks
        
        # Access token cookie (shorter expiration)
        response.set_cookie(
            key="access_token",
            value=access_token,
            max_age=jwt_service.config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            httponly=True,
            secure=True if jwt_service.config.SECURE_COOKIES else False,
            samesite="lax",  # Allow cross-site requests for API calls
            domain=jwt_service.config.COOKIE_DOMAIN,
            path="/api"  # Restrict to API paths only
        )
        
        # Refresh token cookie (longer expiration)
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=jwt_service.config.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            httponly=True,
            secure=True if jwt_service.config.SECURE_COOKIES else False,
            samesite="lax",
            domain=jwt_service.config.COOKIE_DOMAIN,
            path="/api/auth"  # Restrict to auth endpoints only
        )
        
        logger.info(f"User logged in: {user.email} from IP: {client_ip}")
        
        # Return token response
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=expires_in,
            user=UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                full_name=user.full_name,
                role=user.role,
                status=user.status,
                is_verified=user.is_verified,
                avatar_url=user.avatar_url,
                bio=user.bio,
                location=user.location,
                website=user.website,
                preferred_categories=user.preferred_categories,
                risk_tolerance=user.risk_tolerance,
                investment_budget=user.investment_budget,
                created_at=user.created_at,
                last_login=user.last_login
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@auth_router.post("/refresh", response_model=Token)
async def refresh_token(token_refresh: TokenRefresh, request: Request):
    """Refresh access token using refresh token"""
    try:
        # Verify refresh token
        token_data = jwt_service.verify_token(token_refresh.refresh_token, "refresh")
        
        # Check if session exists and is active
        session = await db.user_sessions.find_one({
            "refresh_token": token_refresh.refresh_token,
            "is_active": True,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        # Get user
        user_data = await db.users.find_one({"id": token_data.user_id})
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        user = User(**user_data)
        
        # Check user status
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is not active"
            )
        
        # Create new tokens
        new_token_data = {
            "sub": user.id,
            "email": user.email,
            "role": user.role.value,
            "username": user.username
        }
        
        new_access_token = jwt_service.create_access_token(new_token_data)
        new_refresh_token = jwt_service.create_refresh_token({"sub": user.id, "email": user.email})
        
        # Update session with new refresh token
        await db.user_sessions.update_one(
            {"_id": session["_id"]},
            {
                "$set": {
                    "refresh_token": new_refresh_token,
                    "last_used": datetime.utcnow()
                }
            }
        )
        
        expires_in = jwt_service.config.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        
        logger.info(f"Token refreshed for user: {user.email}")
        
        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=expires_in,
            user=UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                full_name=user.full_name,
                role=user.role,
                status=user.status,
                is_verified=user.is_verified,
                avatar_url=user.avatar_url,
                bio=user.bio,
                location=user.location,
                website=user.website,
                preferred_categories=user.preferred_categories,
                risk_tolerance=user.risk_tolerance,
                investment_budget=user.investment_budget,
                created_at=user.created_at,
                last_login=user.last_login
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@auth_router.post("/logout")
async def logout_user(
    request: Request,
    response: Response,
    current_user = Depends(get_current_user)
):
    """Logout user and invalidate tokens - clears secure httpOnly cookies"""
    try:
        # Invalidate all sessions for this user
        await db.user_sessions.update_many(
            {"user_id": current_user.user_id},
            {"$set": {"is_active": False}}
        )
        
        # Clear both access and refresh token cookies (secure logout)
        response.delete_cookie(
            key="access_token",
            domain=jwt_service.config.COOKIE_DOMAIN,
            path="/api"
        )
        
        response.delete_cookie(
            key="refresh_token",
            domain=jwt_service.config.COOKIE_DOMAIN,
            path="/api/auth"
        )
        
        logger.info(f"User logged out: {current_user.email}")
        
        return {"message": "Successfully logged out", "cookies_cleared": True}
        
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user = Depends(get_current_user)):
    """Get current user profile"""
    try:
        user_data = await db.users.find_one({"id": current_user.user_id})
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = User(**user_data)
        
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            status=user.status,
            is_verified=user.is_verified,
            avatar_url=user.avatar_url,
            bio=user.bio,
            location=user.location,
            website=user.website,
            preferred_categories=user.preferred_categories,
            risk_tolerance=user.risk_tolerance,
            investment_budget=user.investment_budget,
            created_at=user.created_at,
            last_login=user.last_login
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user profile failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )

@auth_router.post("/change-password")
async def change_password(
    password_change: PasswordChange,
    current_user = Depends(get_current_user)
):
    """Change user password"""
    try:
        # Get user
        user_data = await db.users.find_one({"id": current_user.user_id})
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = User(**user_data)
        
        # Verify current password
        if not security_service.verify_password(password_change.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        new_hashed_password = security_service.hash_password(password_change.new_password)
        
        # Update password
        await db.users.update_one(
            {"id": current_user.user_id},
            {
                "$set": {
                    "hashed_password": new_hashed_password,
                    "password_changed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Invalidate all sessions (force re-login)
        await db.user_sessions.update_many(
            {"user_id": current_user.user_id},
            {"$set": {"is_active": False}}
        )
        
        logger.info(f"Password changed for user: {current_user.email}")
        
        return {"message": "Password changed successfully. Please log in again."}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )

@auth_router.get("/sessions")
async def get_user_sessions(current_user = Depends(get_current_user)):
    """Get active sessions for current user"""
    try:
        sessions = await db.user_sessions.find({
            "user_id": current_user.user_id,
            "is_active": True,
            "expires_at": {"$gt": datetime.utcnow()}
        }).to_list(length=None)
        
        # Remove sensitive data
        safe_sessions = []
        for session in sessions:
            safe_sessions.append({
                "id": session["id"],
                "device_info": session.get("device_info", "Unknown"),
                "ip_address": session.get("ip_address", "Unknown"),
                "created_at": session["created_at"],
                "last_used": session["last_used"]
            })
        
        return {"sessions": safe_sessions}
        
    except Exception as e:
        logger.error(f"Get sessions failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get sessions"
        )

@auth_router.delete("/sessions/{session_id}")
async def revoke_session(session_id: str, current_user = Depends(get_current_user)):
    """Revoke a specific session"""
    try:
        result = await db.user_sessions.update_one(
            {
                "id": session_id,
                "user_id": current_user.user_id
            },
            {"$set": {"is_active": False}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return {"message": "Session revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session revocation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session revocation failed"
        )