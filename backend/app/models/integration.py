"""Integration Hub database models for SingleBrief.

This module contains all database models related to the Integration Hub system,
including third-party service integrations, OAuth tokens, and data sources.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (JSON, Boolean, CheckConstraint, Column, DateTime,
                        ForeignKey, Index, Integer, String, Text,
                        UniqueConstraint)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

class Integration(Base):
    """Third-party service integrations configured for organizations.

    This model tracks all external service integrations like Slack, Teams,
    Gmail, Google Drive, etc., with their configuration and status.
    """

    __tablename__ = "integrations"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    configured_by_user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Integration identification
    service_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Service type: slack, teams, gmail, google_drive, github, jira, etc.",
    )
    service_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Human-readable service name"
    )
    integration_key: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Unique key for this integration instance"
    )

    # Configuration
    config: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, comment="Service-specific configuration parameters"
    )
    capabilities: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        comment="List of capabilities: read_messages, send_messages, read_files, etc.",
    )
    scopes: Mapped[List[str]] = mapped_column(
        JSONB, nullable=False, comment="OAuth scopes granted for this integration"
    )

    # Status and health
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        comment="Status: active, inactive, error, pending_auth, expired",
    )
    health_status: Mapped[str] = mapped_column(
        String(20),
        default="healthy",
        comment="Health: healthy, degraded, unhealthy, unknown",
    )
    last_health_check: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Rate limiting and quotas
    rate_limit_per_hour: Mapped[Optional[int]] = mapped_column()
    rate_limit_per_day: Mapped[Optional[int]] = mapped_column()
    quota_used_today: Mapped[int] = mapped_column(default=0)
    quota_reset_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Metadata
    integration_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, comment="Additional service-specific metadata"
    )
    webhook_url: Mapped[Optional[str]] = mapped_column(String(500))
    webhook_secret: Mapped[Optional[str]] = mapped_column(String(255))

    # Privacy and compliance
    data_retention_days: Mapped[Optional[int]] = mapped_column(
        comment="Days to retain data from this integration"
    )
    is_gdpr_compliant: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_required: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="integrations"
    )
    configured_by: Mapped["User"] = relationship(
        "User", back_populates="configured_integrations"
    )
    oauth_tokens: Mapped[List["OAuthToken"]] = relationship(
        "OAuthToken", back_populates="integration", cascade="all, delete-orphan"
    )
    data_sources: Mapped[List["DataSource"]] = relationship(
        "DataSource", back_populates="integration", cascade="all, delete-orphan"
    )
    integration_logs: Mapped[List["IntegrationLog"]] = relationship(
        "IntegrationLog", back_populates="integration", cascade="all, delete-orphan"
    )
    user_permissions: Mapped[List["IntegrationPermission"]] = relationship(
        "IntegrationPermission",
        back_populates="integration",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        Index("idx_integrations_org_service", "organization_id", "service_type"),
        Index("idx_integrations_status", "status"),
        Index("idx_integrations_health", "health_status"),
        Index("idx_integrations_last_sync", "last_sync_at"),
        UniqueConstraint(
            "organization_id", "integration_key", name="uq_org_integration_key"
        ),
        CheckConstraint(
            "service_type IN ('slack', 'teams', 'gmail', 'google_drive', 'google_calendar', "
            "'github', 'jira', 'confluence', 'notion', 'sharepoint', 'onedrive', 'dropbox')",
            name="check_service_type",
        ),
        CheckConstraint(
            "status IN ('active', 'inactive', 'error', 'pending_auth', 'expired')",
            name="check_integration_status",
        ),
        CheckConstraint(
            "health_status IN ('healthy', 'degraded', 'unhealthy', 'unknown')",
            name="check_health_status",
        ),
    )

    def __repr__(self) -> str:
        return f"<Integration(id={self.id}, service={self.service_type}, org_id={self.organization_id})>"

class OAuthToken(Base):
    """OAuth tokens for secure credential storage.

    Stores encrypted OAuth tokens for third-party service authentication
    with proper rotation and expiry management.
    """

    __tablename__ = "oauth_tokens"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    integration_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("integrations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        comment="User-specific token, null for organization-level tokens",
    )

    # Token data (encrypted)
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_encrypted: Mapped[Optional[str]] = mapped_column(Text)
    token_type: Mapped[str] = mapped_column(String(20), default="Bearer")

    # Token metadata
    scopes: Mapped[List[str]] = mapped_column(
        JSONB, nullable=False, comment="Granted OAuth scopes"
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    refresh_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    # External identifiers
    external_user_id: Mapped[Optional[str]] = mapped_column(
        String(255), comment="User ID in the external service"
    )
    external_username: Mapped[Optional[str]] = mapped_column(String(255))
    external_email: Mapped[Optional[str]] = mapped_column(String(255))

    # Token status
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        comment="Status: active, expired, revoked, invalid",
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    usage_count: Mapped[int] = mapped_column(default=0)

    # Encryption metadata
    encryption_key_id: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="ID of encryption key used"
    )
    encryption_algorithm: Mapped[str] = mapped_column(
        String(50), default="AES-256-GCM", comment="Encryption algorithm used"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    integration: Mapped["Integration"] = relationship(
        "Integration", back_populates="oauth_tokens"
    )
    user: Mapped[Optional["User"]] = relationship("User", back_populates="oauth_tokens")

    # Constraints
    __table_args__ = (
        Index("idx_oauth_tokens_integration", "integration_id"),
        Index("idx_oauth_tokens_user", "user_id"),
        Index("idx_oauth_tokens_expires", "expires_at"),
        Index("idx_oauth_tokens_status", "status"),
        Index("idx_oauth_tokens_external_user", "external_user_id"),
        CheckConstraint(
            "status IN ('active', 'expired', 'revoked', 'invalid')",
            name="check_oauth_token_status",
        ),
    )

    def __repr__(self) -> str:
        return f"<OAuthToken(id={self.id}, integration_id={self.integration_id}, status={self.status})>"

class DataSource(Base):
    """External data sources tracked by integrations.

    Tracks specific data sources within integrations (channels, folders,
    repositories) with their sync status and metadata.
    """

    __tablename__ = "data_sources"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    integration_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("integrations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Source identification
    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type: channel, folder, repository, calendar, etc.",
    )
    external_id: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="ID in the external system"
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Source metadata
    source_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, comment="Source-specific metadata and configuration"
    )
    parent_source_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("data_sources.id", ondelete="SET NULL"),
        comment="Parent source for hierarchical structures",
    )

    # Sync configuration
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    sync_frequency: Mapped[str] = mapped_column(
        String(20),
        default="hourly",
        comment="Sync frequency: realtime, hourly, daily, weekly, manual",
    )
    sync_direction: Mapped[str] = mapped_column(
        String(20),
        default="inbound",
        comment="Sync direction: inbound, outbound, bidirectional",
    )

    # Sync status
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    next_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sync_status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        comment="Status: pending, syncing, completed, failed, paused",
    )
    sync_error: Mapped[Optional[str]] = mapped_column(Text)

    # Data statistics
    total_items: Mapped[int] = mapped_column(default=0)
    synced_items: Mapped[int] = mapped_column(default=0)
    failed_items: Mapped[int] = mapped_column(default=0)
    last_item_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Privacy and filtering
    content_filters: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, comment="Content filters applied during sync"
    )
    privacy_level: Mapped[str] = mapped_column(
        String(20),
        default="standard",
        comment="Privacy level: public, standard, sensitive, restricted",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    integration: Mapped["Integration"] = relationship(
        "Integration", back_populates="data_sources"
    )
    parent_source: Mapped[Optional["DataSource"]] = relationship(
        "DataSource", remote_side=[id], back_populates="child_sources"
    )
    child_sources: Mapped[List["DataSource"]] = relationship(
        "DataSource", back_populates="parent_source", cascade="all, delete-orphan"
    )
    sync_logs: Mapped[List["SyncStatus"]] = relationship(
        "SyncStatus", back_populates="data_source", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        Index("idx_data_sources_integration", "integration_id"),
        Index("idx_data_sources_external_id", "external_id"),
        Index("idx_data_sources_type", "source_type"),
        Index("idx_data_sources_sync_status", "sync_status"),
        Index("idx_data_sources_last_sync", "last_sync_at"),
        Index("idx_data_sources_next_sync", "next_sync_at"),
        UniqueConstraint(
            "integration_id", "external_id", name="uq_integration_external_source"
        ),
        CheckConstraint(
            "source_type IN ('channel', 'folder', 'repository', 'calendar', 'board', 'space', 'drive')",
            name="check_source_type",
        ),
        CheckConstraint(
            "sync_frequency IN ('realtime', 'hourly', 'daily', 'weekly', 'manual')",
            name="check_sync_frequency",
        ),
        CheckConstraint(
            "sync_direction IN ('inbound', 'outbound', 'bidirectional')",
            name="check_sync_direction",
        ),
        CheckConstraint(
            "sync_status IN ('pending', 'syncing', 'completed', 'failed', 'paused')",
            name="check_sync_status",
        ),
        CheckConstraint(
            "privacy_level IN ('public', 'standard', 'sensitive', 'restricted')",
            name="check_privacy_level",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<DataSource(id={self.id}, name='{self.name}', type={self.source_type})>"
        )

class IntegrationLog(Base):
    """Logs for integration operations and monitoring.

    Tracks all operations, API calls, and events for integrations
    for monitoring, debugging, and audit purposes.
    """

    __tablename__ = "integration_logs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    integration_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("integrations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Log details
    log_level: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Log level: DEBUG, INFO, WARN, ERROR, CRITICAL",
    )
    operation: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Operation performed: sync, auth, webhook, api_call, etc.",
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Operation details
    operation_id: Mapped[Optional[str]] = mapped_column(
        String(255), comment="Unique ID for grouping related log entries"
    )
    duration_ms: Mapped[Optional[int]] = mapped_column(
        comment="Operation duration in milliseconds"
    )
    status_code: Mapped[Optional[int]] = mapped_column(
        comment="HTTP status code for API operations"
    )

    # Metadata and context
    log_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, comment="Additional context and metadata"
    )
    error_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, comment="Error details and stack traces"
    )

    # External references
    external_request_id: Mapped[Optional[str]] = mapped_column(
        String(255), comment="Request ID from external service"
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    integration: Mapped["Integration"] = relationship(
        "Integration", back_populates="integration_logs"
    )
    user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="integration_logs"
    )

    # Constraints
    __table_args__ = (
        Index(
            "idx_integration_logs_integration_created", "integration_id", "created_at"
        ),
        Index("idx_integration_logs_level", "log_level"),
        Index("idx_integration_logs_operation", "operation"),
        Index("idx_integration_logs_operation_id", "operation_id"),
        Index("idx_integration_logs_created", "created_at"),
        CheckConstraint(
            "log_level IN ('DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL')",
            name="check_log_level",
        ),
    )

    def __repr__(self) -> str:
        return f"<IntegrationLog(id={self.id}, level={self.log_level}, operation='{self.operation}')>"

class SyncStatus(Base):
    """Data source synchronization status tracking.

    Tracks detailed sync status and statistics for data sources
    to monitor sync health and performance.
    """

    __tablename__ = "sync_status"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    data_source_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("data_sources.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Sync execution details
    sync_id: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Unique identifier for this sync run"
    )
    sync_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="Type: full, incremental, manual"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Status: running, completed, failed, cancelled",
    )

    # Timing
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[Optional[int]] = mapped_column()

    # Statistics
    items_processed: Mapped[int] = mapped_column(default=0)
    items_added: Mapped[int] = mapped_column(default=0)
    items_updated: Mapped[int] = mapped_column(default=0)
    items_deleted: Mapped[int] = mapped_column(default=0)
    items_failed: Mapped[int] = mapped_column(default=0)

    # Rate limiting and performance
    api_calls_made: Mapped[int] = mapped_column(default=0)
    rate_limit_hits: Mapped[int] = mapped_column(default=0)
    avg_response_time_ms: Mapped[Optional[float]] = mapped_column()

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    error_count: Mapped[int] = mapped_column(default=0)
    warnings: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, comment="Non-fatal warnings during sync"
    )

    # Checkpoints for resumable syncs
    last_checkpoint: Mapped[Optional[str]] = mapped_column(
        String(255), comment="Last successful checkpoint for resumable syncs"
    )
    checkpoint_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, comment="Data needed to resume sync from checkpoint"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    data_source: Mapped["DataSource"] = relationship(
        "DataSource", back_populates="sync_logs"
    )

    # Constraints
    __table_args__ = (
        Index("idx_sync_status_data_source_started", "data_source_id", "started_at"),
        Index("idx_sync_status_sync_id", "sync_id"),
        Index("idx_sync_status_status", "status"),
        Index("idx_sync_status_started", "started_at"),
        CheckConstraint(
            "sync_type IN ('full', 'incremental', 'manual')", name="check_sync_type"
        ),
        CheckConstraint(
            "status IN ('running', 'completed', 'failed', 'cancelled')",
            name="check_sync_status",
        ),
    )

    def __repr__(self) -> str:
        return f"<SyncStatus(id={self.id}, sync_id='{self.sync_id}', status={self.status})>"

class IntegrationPermission(Base):
    """User permissions for specific integrations.

    Tracks which users have permissions to access specific integrations
    and what level of access they have.
    """

    __tablename__ = "integration_permissions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    integration_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("integrations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    granted_by_user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Permission details
    permission_level: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="Permission level: read, write, admin, none"
    )
    capabilities: Mapped[List[str]] = mapped_column(
        JSONB, nullable=False, comment="Specific capabilities granted"
    )
    restrictions: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, comment="Specific restrictions or limitations"
    )

    # Consent and privacy
    consent_given: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    privacy_level: Mapped[str] = mapped_column(
        String(20),
        default="standard",
        comment="Privacy level: minimal, standard, extended",
    )

    # Permission lifecycle
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    integration: Mapped["Integration"] = relationship(
        "Integration", back_populates="user_permissions"
    )
    user: Mapped["User"] = relationship(
        "User", foreign_keys=[user_id], back_populates="integration_permissions"
    )
    granted_by: Mapped["User"] = relationship("User", foreign_keys=[granted_by_user_id])

    # Constraints
    __table_args__ = (
        Index("idx_integration_permissions_integration", "integration_id"),
        Index("idx_integration_permissions_user", "user_id"),
        Index("idx_integration_permissions_active", "is_active"),
        Index("idx_integration_permissions_expires", "expires_at"),
        UniqueConstraint(
            "integration_id", "user_id", name="uq_integration_user_permission"
        ),
        CheckConstraint(
            "permission_level IN ('read', 'write', 'admin', 'none')",
            name="check_permission_level",
        ),
        CheckConstraint(
            "privacy_level IN ('minimal', 'standard', 'extended')",
            name="check_integration_privacy_level",
        ),
    )

    def __repr__(self) -> str:
        return f"<IntegrationPermission(id={self.id}, integration_id={self.integration_id}, user_id={self.user_id}, level={self.permission_level})>"

class Connector(Base):
    """Plugin connectors for external services.

    Defines available connector plugins that can be installed and configured
    for different external services with versioning and capability tracking.
    """

    __tablename__ = "connectors"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Connector identification
    connector_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Connector type: slack, teams, gmail, etc."
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Human-readable connector name"
    )
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Versioning
    version: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="Semantic version of the connector"
    )
    min_framework_version: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="Minimum required framework version"
    )

    # Connector metadata
    developer: Mapped[str] = mapped_column(String(100), nullable=False)
    homepage_url: Mapped[Optional[str]] = mapped_column(String(500))
    documentation_url: Mapped[Optional[str]] = mapped_column(String(500))
    support_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Capabilities and requirements
    capabilities: Mapped[List[str]] = mapped_column(
        JSONB, nullable=False, comment="List of connector capabilities"
    )
    required_scopes: Mapped[List[str]] = mapped_column(
        JSONB, nullable=False, comment="OAuth scopes required by this connector"
    )
    supported_auth_types: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        comment="Authentication types: oauth2, api_key, basic, custom",
    )

    # Configuration schema
    config_schema: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, comment="JSON schema for connector configuration"
    )
    default_config: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, comment="Default configuration values"
    )

    # Rate limiting defaults
    default_rate_limit_hour: Mapped[Optional[int]] = mapped_column()
    default_rate_limit_day: Mapped[Optional[int]] = mapped_column()
    burst_limit: Mapped[Optional[int]] = mapped_column()

    # Status and lifecycle
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        comment="Status: active, deprecated, archived, experimental",
    )
    is_official: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Whether this is an official connector"
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Whether this connector is verified"
    )

    # Installation and distribution
    package_url: Mapped[Optional[str]] = mapped_column(
        String(500), comment="URL to downloadable package"
    )
    install_script: Mapped[Optional[str]] = mapped_column(
        Text, comment="Installation script or instructions"
    )
    checksum: Mapped[Optional[str]] = mapped_column(
        String(128), comment="Package checksum for verification"
    )

    # Dependencies
    dependencies: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, comment="List of connector dependencies"
    )
    conflicts: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, comment="List of conflicting connectors"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    installations: Mapped[List["ConnectorInstallation"]] = relationship(
        "ConnectorInstallation",
        back_populates="connector",
        cascade="all, delete-orphan",
    )
    health_checks: Mapped[List["ConnectorHealthCheck"]] = relationship(
        "ConnectorHealthCheck", back_populates="connector", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        Index("idx_connectors_type", "connector_type"),
        Index("idx_connectors_status", "status"),
        Index("idx_connectors_version", "version"),
        UniqueConstraint("connector_type", "version", name="uq_connector_type_version"),
        CheckConstraint(
            "status IN ('active', 'deprecated', 'archived', 'experimental')",
            name="check_connector_status",
        ),
    )

    def __repr__(self) -> str:
        return f"<Connector(id={self.id}, type={self.connector_type}, version={self.version})>"

class ConnectorInstallation(Base):
    """Connector installations in organizations.

    Tracks which connectors are installed in which organizations
    with their configuration and update status.
    """

    __tablename__ = "connector_installations"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    connector_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("connectors.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    installed_by_user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Installation details
    installation_config: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, comment="Organization-specific connector configuration"
    )
    environment: Mapped[str] = mapped_column(
        String(20),
        default="production",
        comment="Environment: production, staging, development",
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default="installed",
        comment="Status: installed, updating, disabled, failed, uninstalling",
    )
    health_status: Mapped[str] = mapped_column(
        String(20),
        default="unknown",
        comment="Health: healthy, degraded, unhealthy, unknown",
    )
    last_health_check: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    # Update management
    auto_update: Mapped[bool] = mapped_column(Boolean, default=True)
    update_channel: Mapped[str] = mapped_column(
        String(20), default="stable", comment="Update channel: stable, beta, alpha"
    )
    pending_update_version: Mapped[Optional[str]] = mapped_column(String(20))
    last_update_check: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    # Usage statistics
    total_integrations: Mapped[int] = mapped_column(default=0)
    active_integrations: Mapped[int] = mapped_column(default=0)
    total_api_calls: Mapped[int] = mapped_column(default=0)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Error tracking
    error_count: Mapped[int] = mapped_column(default=0)
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    last_error_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Timestamps
    installed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    connector: Mapped["Connector"] = relationship(
        "Connector", back_populates="installations"
    )
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="connector_installations"
    )
    installed_by: Mapped["User"] = relationship(
        "User", back_populates="connector_installations"
    )
    rate_limits: Mapped[List["RateLimit"]] = relationship(
        "RateLimit",
        back_populates="connector_installation",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        Index("idx_connector_installations_org", "organization_id"),
        Index("idx_connector_installations_connector", "connector_id"),
        Index("idx_connector_installations_status", "status"),
        Index("idx_connector_installations_health", "health_status"),
        UniqueConstraint(
            "connector_id", "organization_id", name="uq_connector_org_installation"
        ),
        CheckConstraint(
            "status IN ('installed', 'updating', 'disabled', 'failed', 'uninstalling')",
            name="check_installation_status",
        ),
        CheckConstraint(
            "health_status IN ('healthy', 'degraded', 'unhealthy', 'unknown')",
            name="check_installation_health_status",
        ),
        CheckConstraint(
            "environment IN ('production', 'staging', 'development')",
            name="check_installation_environment",
        ),
        CheckConstraint(
            "update_channel IN ('stable', 'beta', 'alpha')", name="check_update_channel"
        ),
    )

    def __repr__(self) -> str:
        return f"<ConnectorInstallation(id={self.id}, connector_id={self.connector_id}, org_id={self.organization_id})>"

class ConnectorHealthCheck(Base):
    """Health check results for connectors.

    Tracks health check results and monitoring data for connectors
    to ensure reliability and performance.
    """

    __tablename__ = "connector_health_checks"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    connector_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("connectors.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        comment="Organization-specific health check, null for global",
    )

    # Health check details
    check_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type: connectivity, authentication, quota, performance",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Status: healthy, degraded, unhealthy, unknown",
    )

    # Performance metrics
    response_time_ms: Mapped[Optional[int]] = mapped_column()
    success_rate: Mapped[Optional[float]] = mapped_column()
    error_rate: Mapped[Optional[float]] = mapped_column()
    throughput_per_minute: Mapped[Optional[int]] = mapped_column()

    # Resource usage
    cpu_usage_percent: Mapped[Optional[float]] = mapped_column()
    memory_usage_mb: Mapped[Optional[int]] = mapped_column()
    disk_usage_mb: Mapped[Optional[int]] = mapped_column()
    network_usage_kb: Mapped[Optional[int]] = mapped_column()

    # Health details
    message: Mapped[Optional[str]] = mapped_column(Text)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, comment="Detailed health check results"
    )
    recommendations: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, comment="Health improvement recommendations"
    )

    # Context
    check_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, comment="Additional context and metadata"
    )
    external_service_status: Mapped[Optional[str]] = mapped_column(
        String(50), comment="Status of the external service"
    )

    # Timestamps
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    next_check_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    connector: Mapped["Connector"] = relationship(
        "Connector", back_populates="health_checks"
    )
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization", back_populates="connector_health_checks"
    )

    # Constraints
    __table_args__ = (
        Index(
            "idx_connector_health_checks_connector_checked",
            "connector_id",
            "checked_at",
        ),
        Index("idx_connector_health_checks_org", "organization_id"),
        Index("idx_connector_health_checks_status", "status"),
        Index("idx_connector_health_checks_type", "check_type"),
        CheckConstraint(
            "check_type IN ('connectivity', 'authentication', 'quota', 'performance', 'resource')",
            name="check_health_check_type",
        ),
        CheckConstraint(
            "status IN ('healthy', 'degraded', 'unhealthy', 'unknown')",
            name="check_health_check_status",
        ),
    )

    def __repr__(self) -> str:
        return f"<ConnectorHealthCheck(id={self.id}, connector_id={self.connector_id}, status={self.status})>"

class RateLimit(Base):
    """Rate limiting configuration and tracking.

    Manages rate limits for connector installations with adaptive
    limits and usage tracking.
    """

    __tablename__ = "rate_limits"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    connector_installation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("connector_installations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Rate limit configuration
    limit_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Type: requests_per_minute, requests_per_hour, requests_per_day",
    )
    limit_value: Mapped[int] = mapped_column(
        nullable=False, comment="Maximum number of requests allowed"
    )
    burst_limit: Mapped[Optional[int]] = mapped_column(
        comment="Burst limit for short periods"
    )
    window_seconds: Mapped[int] = mapped_column(
        nullable=False, comment="Time window in seconds"
    )

    # Current usage
    current_usage: Mapped[int] = mapped_column(default=0)
    window_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    last_request_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Adaptive limits
    is_adaptive: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Whether limit adapts based on usage patterns"
    )
    adaptive_factor: Mapped[Optional[float]] = mapped_column(
        comment="Factor for adaptive rate limit adjustments"
    )
    min_limit: Mapped[Optional[int]] = mapped_column(comment="Minimum adaptive limit")
    max_limit: Mapped[Optional[int]] = mapped_column(comment="Maximum adaptive limit")

    # Violation tracking
    violations_count: Mapped[int] = mapped_column(default=0)
    last_violation_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    consecutive_violations: Mapped[int] = mapped_column(default=0)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default="normal",
        comment="Status: normal, warning, critical, suspended",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    connector_installation: Mapped["ConnectorInstallation"] = relationship(
        "ConnectorInstallation", back_populates="rate_limits"
    )

    # Constraints
    __table_args__ = (
        Index("idx_rate_limits_installation", "connector_installation_id"),
        Index("idx_rate_limits_type", "limit_type"),
        Index("idx_rate_limits_window_start", "window_start"),
        Index("idx_rate_limits_active", "is_active"),
        CheckConstraint(
            "limit_type IN ('requests_per_minute', 'requests_per_hour', 'requests_per_day', 'bytes_per_second')",
            name="check_rate_limit_type",
        ),
        CheckConstraint(
            "status IN ('normal', 'warning', 'critical', 'suspended')",
            name="check_rate_limit_status",
        ),
        CheckConstraint("limit_value > 0", name="check_positive_limit_value"),
        CheckConstraint("window_seconds > 0", name="check_positive_window_seconds"),
    )

    def __repr__(self) -> str:
        return f"<RateLimit(id={self.id}, type={self.limit_type}, limit={self.limit_value})>"

class ConfigurationTemplate(Base):
    """Configuration templates for connectors.

    Provides pre-built configuration templates for common
    connector setups and use cases.
    """

    __tablename__ = "configuration_templates"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    connector_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("connectors.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Template identification
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    use_case: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Use case: basic, advanced, enterprise, custom",
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Category: security, performance, compliance, integration",
    )

    # Template configuration
    template_config: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, comment="Template configuration values"
    )
    required_variables: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, comment="Variables that must be provided by user"
    )
    optional_variables: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, comment="Optional variables with defaults"
    )

    # Validation
    validation_rules: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, comment="Validation rules for template configuration"
    )
    dependencies: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, comment="Dependencies required for this template"
    )

    # Usage and popularity
    usage_count: Mapped[int] = mapped_column(default=0)
    rating: Mapped[Optional[float]] = mapped_column()
    is_official: Mapped[bool] = mapped_column(Boolean, default=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)

    # Authorship
    created_by_user_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    organization_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        comment="Organization template belongs to, null for public",
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20), default="active", comment="Status: active, deprecated, archived"
    )
    visibility: Mapped[str] = mapped_column(
        String(20),
        default="public",
        comment="Visibility: public, private, organization",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    connector: Mapped["Connector"] = relationship("Connector")
    created_by: Mapped[Optional["User"]] = relationship(
        "User", back_populates="configuration_templates"
    )
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization", back_populates="configuration_templates"
    )

    # Constraints
    __table_args__ = (
        Index("idx_configuration_templates_connector", "connector_id"),
        Index("idx_configuration_templates_use_case", "use_case"),
        Index("idx_configuration_templates_category", "category"),
        Index("idx_configuration_templates_status", "status"),
        Index("idx_configuration_templates_visibility", "visibility"),
        CheckConstraint(
            "use_case IN ('basic', 'advanced', 'enterprise', 'custom')",
            name="check_template_use_case",
        ),
        CheckConstraint(
            "status IN ('active', 'deprecated', 'archived')",
            name="check_template_status",
        ),
        CheckConstraint(
            "visibility IN ('public', 'private', 'organization')",
            name="check_template_visibility",
        ),
    )

    def __repr__(self) -> str:
        return f"<ConfigurationTemplate(id={self.id}, name='{self.name}', connector_id={self.connector_id})>"
