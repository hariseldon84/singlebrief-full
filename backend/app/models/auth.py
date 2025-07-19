"""
Authentication-related models for tokens and security
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class RefreshToken(Base):
    """Refresh token storage for JWT authentication"""
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Token data
    token_hash = Column(String(255), unique=True, nullable=False)
    jti = Column(String(255), unique=True, nullable=False)  # JWT ID for token rotation
    
    # Device/session info
    device_id = Column(String(255))
    user_agent = Column(Text)
    ip_address = Column(String(45))
    
    # Token status
    is_active = Column(Boolean, default=True)
    is_revoked = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    used_at = Column(DateTime(timezone=True))
    revoked_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<RefreshToken(user_id='{self.user_id}', active='{self.is_active}')>"


class PasswordResetToken(Base):
    """Password reset token storage"""
    __tablename__ = "password_reset_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Token data
    token_hash = Column(String(255), unique=True, nullable=False)
    
    # Security
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Token status
    is_used = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    used_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<PasswordResetToken(user_id='{self.user_id}', used='{self.is_used}')>"


class EmailVerificationToken(Base):
    """Email verification token storage"""
    __tablename__ = "email_verification_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Token data
    token_hash = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), nullable=False)  # Email being verified
    
    # Security
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Token status
    is_used = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    used_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<EmailVerificationToken(user_id='{self.user_id}', email='{self.email}')>"


class LoginAttempt(Base):
    """Login attempt tracking for security monitoring"""
    __tablename__ = "login_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Attempt details
    email = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False, index=True)
    user_agent = Column(Text)
    
    # Result
    success = Column(Boolean, nullable=False)
    failure_reason = Column(String(100))  # Invalid password, account locked, etc.
    
    # User if successful
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    
    # Timestamps
    attempted_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<LoginAttempt(email='{self.email}', success='{self.success}')>"


class APIKey(Base):
    """API keys for programmatic access"""
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Key data
    name = Column(String(200), nullable=False)  # User-provided name
    key_hash = Column(String(255), unique=True, nullable=False)
    key_prefix = Column(String(10), nullable=False)  # First few chars for identification
    
    # Permissions
    scopes = Column(Text)  # JSON array of allowed scopes
    
    # Usage tracking
    last_used = Column(DateTime(timezone=True))
    usage_count = Column(Integer, default=0)
    
    # Key status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<APIKey(name='{self.name}', user_id='{self.user_id}')>"