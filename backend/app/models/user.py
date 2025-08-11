"""
User, Organization, and Team models
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer, String,
                        Table, Text)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

class UserRole(str, Enum):
    """User roles with hierarchical permissions"""

    ADMIN = "admin"  # System administrator
    MANAGER = "manager"  # Team/organization manager
    TEAM_MEMBER = "team_member"  # Regular team member

class ConsentType(str, Enum):
    """Types of consent for privacy controls"""

    DATA_COLLECTION = "data_collection"
    MEMORY_STORAGE = "memory_storage"
    TEAM_SHARING = "team_sharing"
    ANALYTICS = "analytics"
    MARKETING = "marketing"

# Association table for user-team many-to-many relationship
user_team_association = Table(
    "user_team_memberships",
    Base.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), nullable=False),
    Column("team_id", UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False),
    Column("role", String(50), nullable=False, default=UserRole.TEAM_MEMBER),
    Column("joined_at", DateTime(timezone=True), server_default=func.now()),
    Column("is_active", Boolean, default=True),
)

class Organization(Base):
    """Organization model for multi-tenancy"""

    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Clerk integration
    clerk_org_id = Column(String(255), unique=True, nullable=True, index=True)
    
    name = Column(String(200), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    domain = Column(
        String(255), unique=True, nullable=True
    )  # Company domain for auto-assignment
    logo_url = Column(String(500), nullable=True)  # Organization logo

    # Settings
    settings = Column(Text)  # JSON settings for organization
    is_active = Column(Boolean, default=True)

    # Privacy and compliance
    privacy_policy_version = Column(String(20), default="1.0")
    data_retention_days = Column(Integer, default=365)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    users = relationship("User", back_populates="organization")
    teams = relationship("Team", back_populates="organization")

    # New relationships for core models
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation", back_populates="organization"
    )
    decisions: Mapped[List["Decision"]] = relationship(
        "Decision", back_populates="organization"
    )
    user_memories: Mapped[List["UserMemory"]] = relationship(
        "UserMemory", back_populates="organization"
    )
    team_memories: Mapped[List["TeamMemory"]] = relationship(
        "TeamMemory", back_populates="organization"
    )

    # Integration relationships
    integrations: Mapped[List["Integration"]] = relationship(
        "Integration", back_populates="organization"
    )

    # Audit and compliance relationships
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog", back_populates="organization"
    )
    consent_records: Mapped[List["ConsentRecord"]] = relationship(
        "ConsentRecord", back_populates="organization"
    )
    data_access_logs: Mapped[List["DataAccessLog"]] = relationship(
        "DataAccessLog", back_populates="organization"
    )
    privacy_settings: Mapped[List["PrivacySetting"]] = relationship(
        "PrivacySetting", back_populates="organization"
    )
    gdpr_requests: Mapped[List["GDPRRequest"]] = relationship(
        "GDPRRequest", back_populates="organization"
    )
    security_events: Mapped[List["SecurityEvent"]] = relationship(
        "SecurityEvent", back_populates="organization"
    )

    # Authentication relationships  
    oauth_providers: Mapped[List["OAuthProvider"]] = relationship(
        "OAuthProvider", back_populates="organization"
    )
    api_keys: Mapped[List["APIKey"]] = relationship(
        "APIKey", back_populates="organization"
    )

    # Intelligence relationships
    queries: Mapped[List["Query"]] = relationship(
        "Query", back_populates="organization"
    )
    briefs: Mapped[List["Brief"]] = relationship("Brief", back_populates="organization")
    brief_templates: Mapped[List["BriefTemplate"]] = relationship(
        "BriefTemplate", back_populates="organization"
    )
    brief_schedules: Mapped[List["BriefSchedule"]] = relationship(
        "BriefSchedule", back_populates="organization"
    )
    
    # Memory relationships
    user_preferences: Mapped[List["UserPreference"]] = relationship(
        "UserPreference", back_populates="organization"
    )
    user_behavior_patterns: Mapped[List["UserBehaviorPattern"]] = relationship(
        "UserBehaviorPattern", back_populates="organization"
    )
    privacy_consents: Mapped[List["PrivacyConsent"]] = relationship(
        "PrivacyConsent", back_populates="organization"
    )
    data_export_requests: Mapped[List["DataExportRequest"]] = relationship(
        "DataExportRequest", back_populates="organization"
    )
    retention_policies: Mapped[List["DataRetentionPolicy"]] = relationship(
        "DataRetentionPolicy", back_populates="organization"
    )

    # Integration Hub relationships
    connector_installations: Mapped[List["ConnectorInstallation"]] = relationship(
        "ConnectorInstallation", back_populates="organization"
    )
    connector_health_checks: Mapped[List["ConnectorHealthCheck"]] = relationship(
        "ConnectorHealthCheck", back_populates="organization"
    )
    configuration_templates: Mapped[List["ConfigurationTemplate"]] = relationship(
        "ConfigurationTemplate", back_populates="organization"
    )

    def __repr__(self):
        return f"<Organization(name='{self.name}', slug='{self.slug}')>"

class Team(Base):
    """Team model for grouping users"""

    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Organization relationship
    organization_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )

    # Team settings
    is_public = Column(Boolean, default=False)  # Can other org members see this team
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="teams")
    members = relationship(
        "User", secondary=user_team_association, back_populates="teams"
    )

    # New relationships for core models
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation", back_populates="team"
    )
    decisions: Mapped[List["Decision"]] = relationship(
        "Decision", back_populates="team"
    )
    team_memories: Mapped[List["TeamMemory"]] = relationship(
        "TeamMemory", back_populates="team"
    )

    def __repr__(self):
        return f"<Team(name='{self.name}', organization='{self.organization_id}')>"

class User(Base):
    """User model with authentication and profile data"""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Clerk integration
    clerk_user_id = Column(String(255), unique=True, nullable=True, index=True)
    
    # Basic profile
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(200), nullable=False)
    avatar_url = Column(String(500))
    phone = Column(String(20), nullable=True)

    # Authentication
    password_hash = Column(String(255))  # Nullable for OAuth-only users
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Role and permissions
    role = Column(String(50), nullable=False, default=UserRole.TEAM_MEMBER)

    # Organization relationship
    organization_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True
    )

    # OAuth data
    google_id = Column(String(100), unique=True, nullable=True)
    microsoft_id = Column(String(100), unique=True, nullable=True)

    # Security
    last_login = Column(DateTime(timezone=True))
    login_count = Column(Integer, default=0)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))

    # Two-factor authentication
    is_2fa_enabled = Column(Boolean, default=False)
    totp_secret = Column(String(32))  # Base32 encoded TOTP secret
    backup_codes = Column(Text)  # JSON array of backup codes

    # Privacy preferences
    privacy_settings = Column(Text)  # JSON privacy preferences

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="users")
    teams = relationship(
        "Team", secondary=user_team_association, back_populates="members"
    )
    sessions = relationship(
        "UserSession", back_populates="user", cascade="all, delete-orphan"
    )
    consents = relationship(
        "UserConsent", back_populates="user", cascade="all, delete-orphan"
    )

    # New relationships for core models
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation", back_populates="user"
    )
    decisions: Mapped[List["Decision"]] = relationship(
        "Decision", back_populates="user"
    )
    user_memories: Mapped[List["UserMemory"]] = relationship(
        "UserMemory", back_populates="user"
    )
    created_team_memories: Mapped[List["TeamMemory"]] = relationship(
        "TeamMemory", back_populates="created_by"
    )
    preferences: Mapped[List["UserPreference"]] = relationship(
        "UserPreference", back_populates="user"
    )
    behavior_patterns: Mapped[List["UserBehaviorPattern"]] = relationship(
        "UserBehaviorPattern", back_populates="user"
    )
    privacy_consents: Mapped[List["PrivacyConsent"]] = relationship(
        "PrivacyConsent", back_populates="user"
    )
    data_export_requests: Mapped[List["DataExportRequest"]] = relationship(
        "DataExportRequest", back_populates="user"
    )
    retention_policies: Mapped[List["DataRetentionPolicy"]] = relationship(
        "DataRetentionPolicy", back_populates="user"
    )
    team_profile: Mapped[List["TeamMemberProfile"]] = relationship(
        "TeamMemberProfile", back_populates="user"
    )

    # Integration relationships
    configured_integrations: Mapped[List["Integration"]] = relationship(
        "Integration", back_populates="configured_by"
    )
    oauth_tokens: Mapped[List["OAuthToken"]] = relationship(
        "OAuthToken", back_populates="user"
    )
    integration_permissions: Mapped[List["IntegrationPermission"]] = relationship(
        "IntegrationPermission",
        foreign_keys="IntegrationPermission.user_id",
        back_populates="user",
    )
    integration_logs: Mapped[List["IntegrationLog"]] = relationship(
        "IntegrationLog", back_populates="user"
    )

    # Audit and compliance relationships
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog", back_populates="user"
    )
    consent_records: Mapped[List["ConsentRecord"]] = relationship(
        "ConsentRecord", back_populates="user"
    )
    data_access_logs: Mapped[List["DataAccessLog"]] = relationship(
        "DataAccessLog", foreign_keys="DataAccessLog.user_id", back_populates="user"
    )
    privacy_settings: Mapped[List["PrivacySetting"]] = relationship(
        "PrivacySetting", back_populates="user"
    )
    gdpr_requests: Mapped[List["GDPRRequest"]] = relationship(
        "GDPRRequest", foreign_keys="GDPRRequest.user_id", back_populates="user"
    )
    security_events: Mapped[List["SecurityEvent"]] = relationship(
        "SecurityEvent", back_populates="user"
    )

    # Authentication relationships
    auth_sessions: Mapped[List["AuthUserSession"]] = relationship(
        "AuthUserSession", back_populates="user"
    )
    email_verification_tokens: Mapped[List["EmailVerificationToken"]] = relationship(
        "EmailVerificationToken", back_populates="user"
    )
    password_reset_tokens: Mapped[List["PasswordResetToken"]] = relationship(
        "PasswordResetToken", back_populates="user"
    )
    created_api_keys: Mapped[List["APIKey"]] = relationship(
        "APIKey", back_populates="creator"
    )

    # Intelligence relationships
    queries: Mapped[List["Query"]] = relationship("Query", back_populates="user")
    briefs: Mapped[List["Brief"]] = relationship("Brief", back_populates="user")
    brief_templates: Mapped[List["BriefTemplate"]] = relationship(
        "BriefTemplate", back_populates="user"
    )
    brief_schedules: Mapped[List["BriefSchedule"]] = relationship(
        "BriefSchedule", back_populates="user"
    )

    # Integration Hub relationships
    connector_installations: Mapped[List["ConnectorInstallation"]] = relationship(
        "ConnectorInstallation", back_populates="installed_by"
    )
    configuration_templates: Mapped[List["ConfigurationTemplate"]] = relationship(
        "ConfigurationTemplate", back_populates="created_by"
    )

    def __repr__(self):
        return f"<User(email='{self.email}', role='{self.role}')>"

    @property
    def is_locked(self) -> bool:
        """Check if user account is locked"""
        if self.locked_until:
            return datetime.utcnow() < self.locked_until
        return False

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role"""
        return self.role == UserRole.ADMIN

    @property
    def is_manager(self) -> bool:
        """Check if user has manager role or higher"""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]

    def get_team_role(self, team_id: str) -> Optional[str]:
        """Get user's role in a specific team"""
        # This would be implemented with a query to the association table
        # For now, return the global role
        return self.role

class UserTeam(Base):
    """Association model for user-team relationships with additional data"""

    __tablename__ = "user_teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)

    # Role within this specific team
    role = Column(String(50), nullable=False, default=UserRole.TEAM_MEMBER)

    # Membership status
    is_active = Column(Boolean, default=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    left_at = Column(DateTime(timezone=True))

class UserSession(Base):
    """User session tracking for security"""

    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Session data
    session_token = Column(String(255), unique=True, nullable=False)
    refresh_token_hash = Column(String(255))

    # Device/browser info
    user_agent = Column(Text)
    ip_address = Column(String(45))  # IPv6 support
    device_info = Column(Text)  # JSON device fingerprint

    # Session status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="sessions")

    def __repr__(self):
        return f"<UserSession(user_id='{self.user_id}', active='{self.is_active}')>"

class UserConsent(Base):
    """User consent tracking for GDPR compliance"""

    __tablename__ = "user_consents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Consent details
    consent_type = Column(String(50), nullable=False)  # ConsentType enum
    is_granted = Column(Boolean, nullable=False)
    version = Column(String(20), nullable=False)  # Policy version

    # Context
    consent_text = Column(Text)  # What user consented to
    purpose = Column(Text)  # Purpose of data collection

    # Audit trail
    ip_address = Column(String(45))
    user_agent = Column(Text)

    # Timestamps
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))  # Optional expiry
    revoked_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="consents")

    def __repr__(self):
        return f"<UserConsent(user_id='{self.user_id}', type='{self.consent_type}', granted='{self.is_granted}')>"
