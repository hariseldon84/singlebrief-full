"""Audit and compliance database models for SingleBrief.

This module contains all database models related to audit logging,
privacy compliance, and data governance.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, JSON,
    ForeignKey, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class AuditLog(Base):
    """Comprehensive audit logging for all system actions.
    
    Tracks all user actions, system events, and data access for
    compliance, security, and debugging purposes.
    """
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who performed the action, null for system actions"
    )
    organization_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Action details
    action_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Type of action: create, read, update, delete, login, logout, etc."
    )
    resource_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Type of resource: user, conversation, memory, integration, etc."
    )
    resource_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="ID of the specific resource affected"
    )
    
    # Action description and context
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Category: authentication, data_access, privacy, security, system"
    )
    severity: Mapped[str] = mapped_column(
        String(20), 
        default="info",
        comment="Severity level: debug, info, warning, error, critical"
    )
    
    # Request and session context
    session_id: Mapped[Optional[str]] = mapped_column(String(255))
    request_id: Mapped[Optional[str]] = mapped_column(String(255))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    
    # Change tracking
    old_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="Previous values for update operations"
    )
    new_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="New values for create/update operations"
    )
    audit_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="Additional context and metadata"
    )
    
    # Risk and compliance
    risk_level: Mapped[str] = mapped_column(
        String(20), 
        default="low",
        comment="Risk level: low, medium, high, critical"
    )
    compliance_flags: Mapped[Optional[List[str]]] = mapped_column(
        JSONB,
        comment="Compliance framework flags: gdpr, ccpa, hipaa, sox, etc."
    )
    retention_period_days: Mapped[int] = mapped_column(
        default=2555,  # 7 years default
        comment="Days to retain this audit record"
    )
    
    # Success and error tracking
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    error_code: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")
    organization: Mapped[Optional["Organization"]] = relationship("Organization", back_populates="audit_logs")

    # Constraints
    __table_args__ = (
        Index("idx_audit_logs_user_created", "user_id", "created_at"),
        Index("idx_audit_logs_org_created", "organization_id", "created_at"),
        Index("idx_audit_logs_action_type", "action_type"),
        Index("idx_audit_logs_resource", "resource_type", "resource_id"),
        Index("idx_audit_logs_category", "category"),
        Index("idx_audit_logs_severity", "severity"),
        Index("idx_audit_logs_risk", "risk_level"),
        Index("idx_audit_logs_created", "created_at"),
        Index("idx_audit_logs_session", "session_id"),
        CheckConstraint(
            "action_type IN ('create', 'read', 'update', 'delete', 'login', 'logout', "
            "'access', 'export', 'import', 'sync', 'configure', 'grant', 'revoke')",
            name="check_action_type"
        ),
        CheckConstraint(
            "category IN ('authentication', 'data_access', 'privacy', 'security', "
            "'system', 'integration', 'memory', 'billing')",
            name="check_audit_category"
        ),
        CheckConstraint(
            "severity IN ('debug', 'info', 'warning', 'error', 'critical')",
            name="check_audit_severity"
        ),
        CheckConstraint(
            "risk_level IN ('low', 'medium', 'high', 'critical')",
            name="check_risk_level"
        ),
    )

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action_type}, resource={self.resource_type})>"


class ConsentRecord(Base):
    """Privacy consent records for GDPR and data protection compliance.
    
    Tracks all consent given by users for data processing, storage,
    and sharing across different purposes and integrations.
    """
    __tablename__ = "consent_records"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Consent details
    consent_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Type: data_processing, memory_storage, team_sharing, integration_access"
    )
    purpose: Mapped[str] = mapped_column(
        String(100), 
        nullable=False,
        comment="Specific purpose for consent"
    )
    scope: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Scope: user, team, organization, global"
    )
    
    # Consent status
    consent_given: Mapped[bool] = mapped_column(Boolean, nullable=False)
    consent_version: Mapped[str] = mapped_column(
        String(20), 
        nullable=False,
        comment="Version of privacy policy/terms when consent was given"
    )
    consent_method: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Method: explicit_click, implicit_use, email_confirmation, admin_grant"
    )
    
    # Legal basis (GDPR)
    legal_basis: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="GDPR legal basis: consent, contract, legal_obligation, vital_interests, public_task, legitimate_interests"
    )
    
    # Consent metadata
    data_categories: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        comment="Categories of data covered by this consent"
    )
    processing_activities: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        comment="Specific processing activities covered"
    )
    third_parties: Mapped[Optional[List[str]]] = mapped_column(
        JSONB,
        comment="Third parties data may be shared with"
    )
    
    # Geographic and temporal scope
    geographic_scope: Mapped[Optional[List[str]]] = mapped_column(
        JSONB,
        comment="Geographic regions where consent applies"
    )
    retention_period_days: Mapped[Optional[int]] = mapped_column(
        comment="Data retention period in days"
    )
    
    # Withdrawal and revocation
    can_be_withdrawn: Mapped[bool] = mapped_column(Boolean, default=True)
    withdrawal_instructions: Mapped[Optional[str]] = mapped_column(Text)
    withdrawn_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    withdrawal_reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # Timestamps
    given_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="consent_records")
    organization: Mapped["Organization"] = relationship("Organization", back_populates="consent_records")

    # Constraints
    __table_args__ = (
        Index("idx_consent_records_user_type", "user_id", "consent_type"),
        Index("idx_consent_records_org_type", "organization_id", "consent_type"),
        Index("idx_consent_records_given", "consent_given"),
        Index("idx_consent_records_expires", "expires_at"),
        Index("idx_consent_records_created", "created_at"),
        UniqueConstraint("user_id", "consent_type", "purpose", name="uq_user_consent_purpose"),
        CheckConstraint(
            "consent_type IN ('data_processing', 'memory_storage', 'team_sharing', 'integration_access', 'analytics', 'marketing')",
            name="check_consent_type"
        ),
        CheckConstraint(
            "scope IN ('user', 'team', 'organization', 'global')",
            name="check_consent_scope"
        ),
        CheckConstraint(
            "consent_method IN ('explicit_click', 'implicit_use', 'email_confirmation', 'admin_grant', 'api_acceptance')",
            name="check_consent_method"
        ),
        CheckConstraint(
            "legal_basis IN ('consent', 'contract', 'legal_obligation', 'vital_interests', 'public_task', 'legitimate_interests')",
            name="check_legal_basis"
        ),
    )

    def __repr__(self) -> str:
        return f"<ConsentRecord(id={self.id}, type={self.consent_type}, given={self.consent_given})>"


class DataAccessLog(Base):
    """Detailed logging of all data access operations.
    
    Provides transparency by logging every access to user data,
    supporting data subject access requests and privacy audits.
    """
    __tablename__ = "data_access_logs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User whose data was accessed"
    )
    accessed_by_user_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who accessed the data"
    )
    organization_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Access details
    access_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Type: read, export, search, analysis, ai_processing"
    )
    data_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Type of data: memory, conversation, file, integration_data, profile"
    )
    data_source: Mapped[str] = mapped_column(
        String(100), 
        nullable=False,
        comment="Source system or table where data was accessed"
    )
    
    # Context and purpose
    purpose: Mapped[str] = mapped_column(
        String(100), 
        nullable=False,
        comment="Purpose of data access"
    )
    legal_basis: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Legal basis for data access"
    )
    consent_record_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("consent_records.id", ondelete="SET NULL"),
        comment="Related consent record if applicable"
    )
    
    # Access details
    query_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="Details of the query or access pattern"
    )
    data_categories: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        comment="Categories of data accessed"
    )
    record_count: Mapped[Optional[int]] = mapped_column(
        comment="Number of records accessed"
    )
    
    # Technical details
    session_id: Mapped[Optional[str]] = mapped_column(String(255))
    request_id: Mapped[Optional[str]] = mapped_column(String(255))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    
    # Result and performance
    access_granted: Mapped[bool] = mapped_column(Boolean, default=True)
    denial_reason: Mapped[Optional[str]] = mapped_column(Text)
    response_time_ms: Mapped[Optional[int]] = mapped_column()
    
    # Data handling
    data_minimization_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    anonymization_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    encryption_used: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamp
    accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id], back_populates="data_access_logs")
    accessed_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[accessed_by_user_id])
    organization: Mapped[Optional["Organization"]] = relationship("Organization", back_populates="data_access_logs")
    consent_record: Mapped[Optional["ConsentRecord"]] = relationship("ConsentRecord")

    # Constraints
    __table_args__ = (
        Index("idx_data_access_logs_user_accessed", "user_id", "accessed_at"),
        Index("idx_data_access_logs_accessor", "accessed_by_user_id"),
        Index("idx_data_access_logs_type", "access_type"),
        Index("idx_data_access_logs_data_type", "data_type"),
        Index("idx_data_access_logs_accessed", "accessed_at"),
        Index("idx_data_access_logs_session", "session_id"),
        CheckConstraint(
            "access_type IN ('read', 'export', 'search', 'analysis', 'ai_processing', 'backup', 'migration')",
            name="check_data_access_type"
        ),
        CheckConstraint(
            "data_type IN ('memory', 'conversation', 'file', 'integration_data', 'profile', 'audit', 'system')",
            name="check_data_type"
        ),
    )

    def __repr__(self) -> str:
        return f"<DataAccessLog(id={self.id}, type={self.access_type}, data_type={self.data_type})>"


class PrivacySetting(Base):
    """User privacy settings and data control preferences.
    
    Stores individual user preferences for data privacy,
    sharing levels, and privacy controls.
    """
    __tablename__ = "privacy_settings"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Global privacy settings
    privacy_level: Mapped[str] = mapped_column(
        String(20), 
        default="standard",
        comment="Overall privacy level: minimal, standard, enhanced, maximum"
    )
    data_sharing_level: Mapped[str] = mapped_column(
        String(20), 
        default="team",
        comment="Data sharing level: private, team, organization, none"
    )
    
    # Memory and conversation settings
    memory_retention: Mapped[bool] = mapped_column(Boolean, default=True)
    memory_sharing_with_team: Mapped[bool] = mapped_column(Boolean, default=False)
    conversation_retention_days: Mapped[Optional[int]] = mapped_column(
        default=365,
        comment="Days to retain conversations, null for indefinite"
    )
    
    # AI and processing settings
    ai_training_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    analytics_consent: Mapped[bool] = mapped_column(Boolean, default=True)
    personalization_consent: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Integration and external sharing
    external_integration_consent: Mapped[bool] = mapped_column(Boolean, default=True)
    third_party_sharing_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    cross_border_transfer_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Notification preferences
    privacy_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    data_access_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    consent_expiry_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Data subject rights preferences
    auto_data_export: Mapped[bool] = mapped_column(Boolean, default=False)
    data_export_format: Mapped[str] = mapped_column(
        String(20), 
        default="json",
        comment="Preferred export format: json, csv, pdf"
    )
    
    # Custom privacy preferences
    custom_settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="Custom privacy settings and preferences"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="privacy_settings")
    organization: Mapped["Organization"] = relationship("Organization", back_populates="privacy_settings")

    # Constraints
    __table_args__ = (
        Index("idx_privacy_settings_user", "user_id"),
        Index("idx_privacy_settings_org", "organization_id"),
        Index("idx_privacy_settings_level", "privacy_level"),
        UniqueConstraint("user_id", "organization_id", name="uq_user_org_privacy_settings"),
        CheckConstraint(
            "privacy_level IN ('minimal', 'standard', 'enhanced', 'maximum')",
            name="check_privacy_level"
        ),
        CheckConstraint(
            "data_sharing_level IN ('private', 'team', 'organization', 'none')",
            name="check_data_sharing_level"
        ),
        CheckConstraint(
            "data_export_format IN ('json', 'csv', 'pdf', 'xml')",
            name="check_data_export_format"
        ),
    )

    def __repr__(self) -> str:
        return f"<PrivacySetting(id={self.id}, user_id={self.user_id}, level={self.privacy_level})>"


class GDPRRequest(Base):
    """GDPR data subject rights requests.
    
    Tracks and manages all GDPR data subject access requests (DSAR),
    data portability, rectification, and erasure requests.
    """
    __tablename__ = "gdpr_requests"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False
    )
    handled_by_user_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Request details
    request_type: Mapped[str] = mapped_column(
        String(30), 
        nullable=False,
        comment="Type: access, portability, rectification, erasure, restriction, objection"
    )
    request_reference: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        unique=True,
        comment="Unique reference number for the request"
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Request scope
    data_categories: Mapped[Optional[List[str]]] = mapped_column(
        JSONB,
        comment="Specific data categories requested"
    )
    date_range_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    date_range_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Status and processing
    status: Mapped[str] = mapped_column(
        String(20), 
        default="submitted",
        comment="Status: submitted, validated, processing, completed, rejected, cancelled"
    )
    priority: Mapped[str] = mapped_column(
        String(20), 
        default="standard",
        comment="Priority: low, standard, high, urgent"
    )
    
    # Legal and compliance
    legal_basis_verification: Mapped[bool] = mapped_column(Boolean, default=False)
    identity_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_method: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Processing details
    estimated_completion_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    actual_completion_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    processing_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Response and delivery
    response_format: Mapped[str] = mapped_column(
        String(20), 
        default="json",
        comment="Response format: json, csv, pdf, email"
    )
    response_method: Mapped[str] = mapped_column(
        String(20), 
        default="download",
        comment="Delivery method: download, email, secure_portal"
    )
    response_delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    response_file_path: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Communication
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    communication_preference: Mapped[str] = mapped_column(
        String(20), 
        default="email",
        comment="Communication preference: email, phone, secure_message"
    )
    
    # Timestamps
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    started_processing_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="gdpr_requests")
    handled_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[handled_by_user_id])
    organization: Mapped["Organization"] = relationship("Organization", back_populates="gdpr_requests")

    # Constraints
    __table_args__ = (
        Index("idx_gdpr_requests_user", "user_id"),
        Index("idx_gdpr_requests_org", "organization_id"),
        Index("idx_gdpr_requests_type", "request_type"),
        Index("idx_gdpr_requests_status", "status"),
        Index("idx_gdpr_requests_submitted", "submitted_at"),
        Index("idx_gdpr_requests_reference", "request_reference"),
        CheckConstraint(
            "request_type IN ('access', 'portability', 'rectification', 'erasure', 'restriction', 'objection')",
            name="check_gdpr_request_type"
        ),
        CheckConstraint(
            "status IN ('submitted', 'validated', 'processing', 'completed', 'rejected', 'cancelled')",
            name="check_gdpr_status"
        ),
        CheckConstraint(
            "priority IN ('low', 'standard', 'high', 'urgent')",
            name="check_gdpr_priority"
        ),
        CheckConstraint(
            "response_format IN ('json', 'csv', 'pdf', 'xml', 'email')",
            name="check_response_format"
        ),
        CheckConstraint(
            "response_method IN ('download', 'email', 'secure_portal', 'physical_mail')",
            name="check_response_method"
        ),
    )

    def __repr__(self) -> str:
        return f"<GDPRRequest(id={self.id}, type={self.request_type}, ref={self.request_reference})>"


class SecurityEvent(Base):
    """Security events and threat monitoring.
    
    Logs security-related events for threat detection,
    incident response, and security analytics.
    """
    __tablename__ = "security_events"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    organization_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Event classification
    event_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Type: authentication, authorization, data_access, system, network"
    )
    event_category: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Category: failed_login, privilege_escalation, data_breach, etc."
    )
    severity: Mapped[str] = mapped_column(
        String(20), 
        default="info",
        comment="Severity: info, low, medium, high, critical"
    )
    
    # Event details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_system: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Technical details
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    session_id: Mapped[Optional[str]] = mapped_column(String(255))
    request_id: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Threat intelligence
    threat_indicators: Mapped[Optional[List[str]]] = mapped_column(
        JSONB,
        comment="Threat indicators and IOCs"
    )
    risk_score: Mapped[float] = mapped_column(
        default=0.0,
        comment="Risk score 0.0-10.0"
    )
    confidence_score: Mapped[float] = mapped_column(
        default=0.5,
        comment="Confidence in threat assessment 0.0-1.0"
    )
    
    # Response and mitigation
    response_status: Mapped[str] = mapped_column(
        String(20), 
        default="open",
        comment="Status: open, investigating, mitigated, resolved, false_positive"
    )
    response_actions: Mapped[Optional[List[str]]] = mapped_column(
        JSONB,
        comment="Actions taken in response to the event"
    )
    assigned_to: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Additional data
    event_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="Additional event metadata and context"
    )
    
    # Timestamps
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="security_events")
    organization: Mapped[Optional["Organization"]] = relationship("Organization", back_populates="security_events")

    # Constraints
    __table_args__ = (
        Index("idx_security_events_user", "user_id"),
        Index("idx_security_events_org", "organization_id"),
        Index("idx_security_events_type", "event_type"),
        Index("idx_security_events_category", "event_category"),
        Index("idx_security_events_severity", "severity"),
        Index("idx_security_events_occurred", "occurred_at"),
        Index("idx_security_events_risk", "risk_score"),
        Index("idx_security_events_status", "response_status"),
        CheckConstraint(
            "event_type IN ('authentication', 'authorization', 'data_access', 'system', 'network', 'application')",
            name="check_security_event_type"
        ),
        CheckConstraint(
            "severity IN ('info', 'low', 'medium', 'high', 'critical')",
            name="check_security_severity"
        ),
        CheckConstraint(
            "response_status IN ('open', 'investigating', 'mitigated', 'resolved', 'false_positive')",
            name="check_response_status"
        ),
        CheckConstraint(
            "risk_score >= 0.0 AND risk_score <= 10.0",
            name="check_risk_score_range"
        ),
        CheckConstraint(
            "confidence_score >= 0.0 AND confidence_score <= 1.0",
            name="check_security_confidence_range"
        ),
    )

    def __repr__(self) -> str:
        return f"<SecurityEvent(id={self.id}, type={self.event_type}, severity={self.severity})>"