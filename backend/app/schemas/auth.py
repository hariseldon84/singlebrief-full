"""
Authentication API schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, validator
from app.core.security import validate_password_strength


class UserRegister(BaseModel):
    """User registration schema"""
    email: EmailStr
    password: str
    full_name: str
    organization_name: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        if not validate_password_strength(v):
            raise ValueError(
                'Password must be at least 12 characters with uppercase, '
                'lowercase, numbers, and special characters'
            )
        return v
    
    @validator('full_name')
    def validate_full_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Full name must be at least 2 characters')
        return v.strip()


class UserLogin(BaseModel):
    """User login schema"""
    email: EmailStr
    password: str
    remember_me: bool = False
    device_info: Optional[str] = None


class OAuthLogin(BaseModel):
    """OAuth login schema"""
    provider: str  # 'google' or 'microsoft'
    code: str
    state: str
    redirect_uri: str


class Token(BaseModel):
    """JWT token data"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenResponse(BaseModel):
    """Complete authentication response"""
    user: "UserResponse"
    tokens: Token
    organization: Optional["OrganizationResponse"] = None
    teams: List["TeamResponse"] = []


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class PasswordReset(BaseModel):
    """Password reset request"""
    email: EmailStr


class PasswordChange(BaseModel):
    """Password change with reset token"""
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if not validate_password_strength(v):
            raise ValueError(
                'Password must be at least 12 characters with uppercase, '
                'lowercase, numbers, and special characters'
            )
        return v


class EmailVerification(BaseModel):
    """Email verification"""
    token: str


class ResendVerification(BaseModel):
    """Resend verification email"""
    email: EmailStr


class ChangePassword(BaseModel):
    """Change password for authenticated user"""
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if not validate_password_strength(v):
            raise ValueError(
                'Password must be at least 12 characters with uppercase, '
                'lowercase, numbers, and special characters'
            )
        return v


class TwoFactorSetup(BaseModel):
    """Two-factor authentication setup"""
    totp_code: str


class TwoFactorVerify(BaseModel):
    """Two-factor authentication verification"""
    email: EmailStr
    password: str
    totp_code: str
    remember_me: bool = False


class APIKeyCreate(BaseModel):
    """API key creation"""
    name: str
    scopes: List[str] = []
    expires_at: Optional[datetime] = None


class APIKeyResponse(BaseModel):
    """API key response"""
    id: str
    name: str
    key: str  # Only returned on creation
    key_prefix: str
    scopes: List[str]
    created_at: datetime
    expires_at: Optional[datetime]
    
    class Config:
        orm_mode = True


# Forward references for circular imports
from .user import UserResponse, OrganizationResponse, TeamResponse
TokenResponse.model_rebuild()