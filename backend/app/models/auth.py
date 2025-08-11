"""Authentication system database models for SingleBrief.

This module contains all database models related to OAuth providers,
user sessions, and API keys for authentication and authorization.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (JSON, Boolean, CheckConstraint, Column, DateTime,
                        ForeignKey, Index, Integer, String, Text)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class OAuthProvider(Base):
    """OAuth provider configurations for organizations.
    
    Stores OAuth client configurations for Google, Microsoft, Slack, etc.
    Each organization can configure multiple OAuth providers.
    """
    
    __tablename__ = "oauth_providers"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Provider configuration
    provider_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="OAuth provider type: google, microsoft, slack, github",
    )
    provider_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Human-readable provider name for UI display",
    )
    
    # OAuth credentials
    client_id: Mapped[str] = mapped_column(String(255), nullable=False)
    client_secret_encrypted: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Encrypted OAuth client secret",
    )
    
    # Provider settings
    scopes: Mapped[List[str]] = mapped_column(
        JSONB,
        default=lambda: ["email", "profile"],
        comment="OAuth scopes to request",
    )
    provider_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Provider-specific configuration (tenant_id, domain, etc.)",
    )
    
    # Status and metadata
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="oauth_providers"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "provider_type IN ('google', 'microsoft', 'slack', 'github')",
            name="valid_provider_type",
        ),
        Index("idx_oauth_providers_org_type", "organization_id", "provider_type"),
        Index("idx_oauth_providers_enabled", "is_enabled"),
    )


class AuthUserSession(Base):
    """User authentication sessions with refresh tokens.
    
    Tracks user sessions for security monitoring and token management.
    Each session represents a user login on a specific device/browser.
    """
    
    __tablename__ = "auth_user_sessions"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Token management
    refresh_token_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        comment="Bcrypt hash of refresh token",
    )
    
    # Session metadata
    device_info: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        default=lambda: {},
        comment="Device fingerprint and browser info",
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        INET,
        nullable=True,
        comment="IP address when session was created",
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Browser user agent string",
    )
    
    # Session lifecycle
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="When refresh token expires",
    )
    last_used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        comment="Last time this session was used",
    )
    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Whether session has been manually revoked",
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="auth_sessions")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_user_sessions_user_id", "user_id"),
        Index("idx_user_sessions_expires_at", "expires_at"),
        Index("idx_user_sessions_token_hash", "refresh_token_hash"),
        Index("idx_user_sessions_active", "user_id", "is_revoked", "expires_at"),
    )


class APIKey(Base):
    """API keys for service-to-service authentication.
    
    Allows external services and scripts to authenticate with SingleBrief API
    using long-lived API keys instead of user tokens.
    """
    
    __tablename__ = "api_keys"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_by: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # API key details
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Human-readable name for the API key",
    )
    key_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        comment="Bcrypt hash of the actual API key",
    )
    key_prefix: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        comment="First 8 characters of key for identification",
    )
    
    # Permissions and scope
    permissions: Mapped[List[str]] = mapped_column(
        JSONB,
        default=lambda: [],
        comment="List of permissions granted to this API key",
    )
    allowed_ips: Mapped[Optional[List[str]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="IP addresses/CIDR blocks allowed to use this key",
    )
    
    # Lifecycle management
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When API key expires (null = never)",
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last time this API key was used",
    )
    usage_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Number of times this key has been used",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Whether this API key is currently active",
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="api_keys"
    )
    creator: Mapped["User"] = relationship("User", back_populates="created_api_keys")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_api_keys_org_id", "organization_id"),
        Index("idx_api_keys_key_hash", "key_hash"),
        Index("idx_api_keys_prefix", "key_prefix"),
        Index("idx_api_keys_active", "is_active", "expires_at"),
        Index("idx_api_keys_creator", "created_by"),
    )


class LoginAttempt(Base):
    """Failed login attempt tracking for security monitoring.
    
    Tracks failed authentication attempts for rate limiting and security
    monitoring. Used to implement account lockout and suspicious activity detection.
    """
    
    __tablename__ = "login_attempts"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    
    # Attempt details
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Email attempted (may not exist in system)",
    )
    ip_address: Mapped[str] = mapped_column(
        INET,
        nullable=False,
        comment="IP address of the attempt",
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Browser user agent string",
    )
    
    # Attempt results
    attempt_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type of attempt: email_password, oauth, api_key",
    )
    failure_reason: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Why the attempt failed: invalid_credentials, account_locked, etc.",
    )
    was_successful: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Whether this attempt succeeded",
    )
    
    # Additional context
    additional_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional context about the attempt",
    )
    
    # Timestamps
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    
    # Indexes for security queries
    __table_args__ = (
        CheckConstraint(
            "attempt_type IN ('email_password', 'oauth', 'api_key')",
            name="valid_attempt_type",
        ),
        Index("idx_login_attempts_email_time", "email", "attempted_at"),
        Index("idx_login_attempts_ip_time", "ip_address", "attempted_at"),
        Index("idx_login_attempts_success", "was_successful", "attempted_at"),
        Index("idx_login_attempts_cleanup", "attempted_at"),  # For cleanup jobs
    )


class EmailVerificationToken(Base):
    """Email verification tokens for new user registration."""
    
    __tablename__ = "email_verification_tokens"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="email_verification_tokens")


class PasswordResetToken(Base):
    """Password reset tokens for users."""
    
    __tablename__ = "password_reset_tokens"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="password_reset_tokens")


# Alias for compatibility
RefreshToken = AuthUserSession