"""
Security utilities for authentication and authorization
"""

import secrets
import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from fastapi import HTTPException, status
from pydantic import BaseModel
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

# Password context for hashing and verification
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Algorithm
ALGORITHM = "HS256"

class TokenData(BaseModel):
    user_id: str
    email: str
    role: str
    organization_id: Optional[str] = None
    team_ids: list[str] = []
    permissions: list[str] = []
    exp: Optional[datetime] = None


def hash_password(password: str) -> str:
    """Hash a password using bcrypt with salt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def generate_password_reset_token() -> str:
    """Generate a secure random token for password reset"""
    return secrets.token_urlsafe(32)


def validate_password_strength(password: str) -> bool:
    """Validate password meets security requirements"""
    if len(password) < 12:
        return False
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    return all([has_upper, has_lower, has_digit, has_special])


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, expected_type: str = "access") -> TokenData:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check token type
        if payload.get("type") != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # Check expiration
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        
        # Extract token data
        token_data = TokenData(
            user_id=payload.get("sub"),
            email=payload.get("email"),
            role=payload.get("role"),
            organization_id=payload.get("organization_id"),
            team_ids=payload.get("team_ids", []),
            permissions=payload.get("permissions", []),
            exp=datetime.fromtimestamp(exp) if exp else None
        )
        
        return token_data
        
    except jwt.PyJWTError as e:
        logger.error("JWT decode error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


def create_email_verification_token(email: str) -> str:
    """Create a token for email verification"""
    data = {"email": email, "type": "email_verification"}
    expire = datetime.utcnow() + timedelta(hours=24)  # 24 hour expiry
    data.update({"exp": expire})
    
    return jwt.encode(data, settings.SECRET_KEY, algorithm=ALGORITHM)


def verify_email_verification_token(token: str) -> str:
    """Verify email verification token and return email"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("type") != "email_verification":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type"
            )
        
        email = payload.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token"
            )
        
        return email
        
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )


def generate_api_key() -> str:
    """Generate a secure API key"""
    return secrets.token_urlsafe(40)


def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage"""
    return hash_password(api_key)


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash"""
    return verify_password(plain_key, hashed_key)


class RateLimiter:
    """Rate limiting utilities"""
    
    @staticmethod
    def get_client_ip(request) -> str:
        """Extract client IP address from request"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host
    
    @staticmethod
    def create_rate_limit_key(identifier: str, endpoint: str) -> str:
        """Create a rate limit key for Redis"""
        return f"rate_limit:{endpoint}:{identifier}"


# Security headers for API responses
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin"
}