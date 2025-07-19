"""
Authentication dependencies and middleware
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import structlog

from app.core.database import get_db_session
from app.core.security import verify_token, TokenData
from app.models.user import User, UserRole
from app.models.auth import RefreshToken, LoginAttempt

logger = structlog.get_logger(__name__)

# HTTP Bearer token security
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """Get current authenticated user from JWT token"""
    try:
        # Verify and decode the token
        token_data: TokenData = verify_token(credentials.credentials)
        
        # Fetch user from database
        result = await db.execute(
            select(User).where(User.id == token_data.user_id)
        )
        user = result.scalar_one_or_none()
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user"
            )
        
        if user.is_locked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is locked"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Authentication error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user (additional check for active status)"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current verified user"""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified"
        )
    return current_user


def require_role(required_role: UserRole):
    """Dependency factory for role-based access control"""
    async def role_checker(current_user: User = Depends(get_current_verified_user)) -> User:
        if required_role == UserRole.ADMIN and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        elif required_role == UserRole.MANAGER and current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Manager access required"
            )
        return current_user
    
    return role_checker


def require_admin(current_user: User = Depends(get_current_verified_user)) -> User:
    """Require admin role"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def require_manager(current_user: User = Depends(get_current_verified_user)) -> User:
    """Require manager role or higher"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager access required"
        )
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db_session)
) -> Optional[User]:
    """Get current user if authenticated, otherwise None"""
    if not credentials:
        return None
    
    try:
        token_data: TokenData = verify_token(credentials.credentials)
        result = await db.execute(
            select(User).where(User.id == token_data.user_id)
        )
        user = result.scalar_one_or_none()
        
        if user and user.is_active and not user.is_locked:
            return user
    except Exception:
        pass
    
    return None


async def verify_refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """Verify refresh token and return user"""
    try:
        # Verify token structure
        token_data = verify_token(refresh_token, expected_type="refresh")
        
        # Check if refresh token exists and is valid
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == token_data.user_id,
                RefreshToken.is_active == True,
                RefreshToken.is_revoked == False
            )
        )
        db_token = result.scalar_one_or_none()
        
        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user
        result = await db.execute(
            select(User).where(User.id == token_data.user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Refresh token verification error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


async def log_login_attempt(
    email: str,
    ip_address: str,
    user_agent: str,
    success: bool,
    user_id: Optional[str] = None,
    failure_reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """Log login attempt for security monitoring"""
    try:
        login_attempt = LoginAttempt(
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            user_id=user_id,
            failure_reason=failure_reason
        )
        db.add(login_attempt)
        await db.commit()
        
    except Exception as e:
        logger.error("Failed to log login attempt", error=str(e))
        # Don't fail the request if logging fails
        pass


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host


def get_user_agent(request: Request) -> str:
    """Extract user agent from request"""
    return request.headers.get("User-Agent", "Unknown")