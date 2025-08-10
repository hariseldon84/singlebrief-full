"""
Team Management Models for Story 7.1

Comprehensive team member profile management system including:
- Enhanced team member profiles with roles, designations, custom tags
- Team hierarchy and relationship mapping  
- Status and contact preference management
- Platform integration and account linking
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (JSON, Boolean, Column, DateTime, Float, ForeignKey,
                        Index, Integer, String, Text, UniqueConstraint)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base


class MemberStatus(str, Enum):
    """Team member status options"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"
    PENDING_INVITATION = "pending_invitation"
    SUSPENDED = "suspended"


class ContactPreference(str, Enum):
    """Contact method preferences"""
    IN_APP = "in_app"
    EMAIL = "email"
    SLACK = "slack"
    TEAMS = "teams"
    DISABLED = "disabled"


class PlatformType(str, Enum):
    """External platform types for integration"""
    SLACK = "slack"
    MICROSOFT_TEAMS = "teams"
    EMAIL = "email"
    GOOGLE_WORKSPACE = "google_workspace"


class HierarchyRelationType(str, Enum):
    """Types of hierarchical relationships"""
    MANAGER = "manager"
    DIRECT_REPORT = "direct_report"
    TEAM_LEAD = "team_lead"
    PEER = "peer"
    COLLABORATOR = "collaborator"


class RoleTaxonomy(Base):
    """Predefined and custom role definitions for team members"""
    
    __tablename__ = "role_taxonomy"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Role metadata
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # engineering, design, product, etc.
    seniority_level: Mapped[Optional[str]] = mapped_column(String(50))  # junior, mid, senior, lead, principal
    
    # System vs custom roles
    is_system_role: Mapped[bool] = mapped_column(Boolean, default=False)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True
    )
    
    # Role permissions and capabilities
    default_permissions: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    suggested_tags: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    # Relationships
    team_members = relationship("TeamMemberProfileManagement", back_populates="role")
    
    __table_args__ = (
        Index("idx_role_taxonomy_category", "category"),
        Index("idx_role_taxonomy_org", "organization_id"),
        UniqueConstraint("name", "organization_id", name="uq_role_taxonomy_name_org"),
    )


class DesignationTaxonomy(Base):
    """Predefined and custom designations for team members"""
    
    __tablename__ = "designation_taxonomy"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Designation metadata
    hierarchy_level: Mapped[int] = mapped_column(Integer, default=0)  # 0=lowest, higher=more senior
    department: Mapped[Optional[str]] = mapped_column(String(100))
    
    # System vs custom designations
    is_system_designation: Mapped[bool] = mapped_column(Boolean, default=False)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True
    )
    
    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    # Relationships
    team_members = relationship("TeamMemberProfileManagement", back_populates="designation")
    
    __table_args__ = (
        Index("idx_designation_taxonomy_hierarchy", "hierarchy_level"),
        Index("idx_designation_taxonomy_org", "organization_id"),
        UniqueConstraint("name", "organization_id", name="uq_designation_taxonomy_name_org"),
    )


class ExpertiseTag(Base):
    """Custom expertise tags for team member skills and knowledge areas"""
    
    __tablename__ = "expertise_tags"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Tag categorization
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # technical, domain, soft_skills, etc.
    color: Mapped[Optional[str]] = mapped_column(String(7))  # hex color for UI display
    
    # System vs custom tags
    is_system_tag: Mapped[bool] = mapped_column(Boolean, default=False)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True
    )
    
    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    __table_args__ = (
        Index("idx_expertise_tags_category", "category"),
        Index("idx_expertise_tags_org", "organization_id"),
        Index("idx_expertise_tags_usage", "usage_count"),
        UniqueConstraint("name", "organization_id", name="uq_expertise_tags_name_org"),
    )


class TeamMemberProfileManagement(Base):
    """Comprehensive team member profile for management and query routing"""
    
    __tablename__ = "team_member_profiles_management"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    
    # Basic information
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(150), nullable=False)
    
    # Core relationships
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    
    # Role and designation
    role_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("role_taxonomy.id"), nullable=True
    )
    designation_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("designation_taxonomy.id"), nullable=True
    )
    
    # Custom role/designation if not from taxonomy
    custom_role: Mapped[Optional[str]] = mapped_column(String(150))
    custom_designation: Mapped[Optional[str]] = mapped_column(String(150))
    
    # Profile information
    profile_photo_url: Mapped[Optional[str]] = mapped_column(String(500))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    location: Mapped[Optional[str]] = mapped_column(String(200))
    timezone: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Contact information
    work_phone: Mapped[Optional[str]] = mapped_column(String(50))
    mobile_phone: Mapped[Optional[str]] = mapped_column(String(50))
    secondary_email: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Status and availability
    status: Mapped[MemberStatus] = mapped_column(String(50), default=MemberStatus.ACTIVE)
    availability_status: Mapped[Optional[str]] = mapped_column(String(100))  # Available, Busy, In Meeting, etc.
    
    # Workload and capacity
    current_workload: Mapped[float] = mapped_column(Float, default=0.5)  # 0.0 = light, 1.0 = maximum
    capacity_percentage: Mapped[int] = mapped_column(Integer, default=100)  # % of full-time
    
    # Expertise and skills
    skills_summary: Mapped[Optional[str]] = mapped_column(Text)
    years_experience: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Contact preferences - primary method for each type of communication
    query_contact_preference: Mapped[ContactPreference] = mapped_column(
        String(20), default=ContactPreference.IN_APP
    )
    urgent_contact_preference: Mapped[ContactPreference] = mapped_column(
        String(20), default=ContactPreference.EMAIL
    )
    notification_preference: Mapped[ContactPreference] = mapped_column(
        String(20), default=ContactPreference.EMAIL
    )
    
    # Communication settings
    response_time_expectation_hours: Mapped[int] = mapped_column(Integer, default=24)
    working_hours_start: Mapped[Optional[str]] = mapped_column(String(5))  # HH:MM format
    working_hours_end: Mapped[Optional[str]] = mapped_column(String(5))  # HH:MM format
    working_days: Mapped[List[str]] = mapped_column(JSON, default=list)  # ["monday", "tuesday", ...]
    
    # Platform integration status
    slack_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    teams_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Performance and interaction metrics
    total_queries_received: Mapped[int] = mapped_column(Integer, default=0)
    total_queries_responded: Mapped[int] = mapped_column(Integer, default=0)
    average_response_time_hours: Mapped[float] = mapped_column(Float, default=0.0)
    response_quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Invitation and onboarding
    invitation_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    invitation_accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    onboarded_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Admin fields
    notes: Mapped[Optional[str]] = mapped_column(Text)  # Admin notes about this team member
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    # Relationships
    user = relationship("User")
    team = relationship("Team")
    organization = relationship("Organization")
    role = relationship("RoleTaxonomy", back_populates="team_members")
    designation = relationship("DesignationTaxonomy", back_populates="team_members")
    
    # Expertise tags (many-to-many)
    expertise_tags = relationship(
        "ExpertiseTag",
        secondary="team_member_expertise_tags",
        back_populates="team_members"
    )
    
    # Platform accounts
    platform_accounts = relationship(
        "TeamMemberPlatformAccount",
        back_populates="team_member",
        cascade="all, delete-orphan"
    )
    
    # Hierarchical relationships
    subordinates = relationship(
        "TeamHierarchy",
        foreign_keys="TeamHierarchy.manager_id",
        back_populates="manager"
    )
    managers = relationship(
        "TeamHierarchy", 
        foreign_keys="TeamHierarchy.subordinate_id",
        back_populates="subordinate"
    )
    
    __table_args__ = (
        Index("idx_team_member_profile_mgmt_team", "team_id"),
        Index("idx_team_member_profile_mgmt_user", "user_id"),
        Index("idx_team_member_profile_mgmt_status", "status"),
        Index("idx_team_member_profile_mgmt_org", "organization_id"),
        UniqueConstraint("user_id", "team_id", name="uq_team_member_profile_mgmt_user_team"),
    )


# Many-to-many association table for team member expertise tags
from sqlalchemy import Table
team_member_expertise_tags = Table(
    "team_member_expertise_tags",
    Base.metadata,
    Column("team_member_id", UUID(as_uuid=False), ForeignKey("team_member_profiles_management.id"), primary_key=True),
    Column("expertise_tag_id", UUID(as_uuid=False), ForeignKey("expertise_tags.id"), primary_key=True),
    Column("proficiency_level", Integer, default=3),  # 1-5 scale
    Column("created_at", DateTime, default=datetime.utcnow),
)

# Update ExpertiseTag model to include the relationship
ExpertiseTag.team_members = relationship(
    "TeamMemberProfileManagement",
    secondary=team_member_expertise_tags,
    back_populates="expertise_tags"
)


class TeamMemberPlatformAccount(Base):
    """Platform account integration and verification for team members"""
    
    __tablename__ = "team_member_platform_accounts"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    team_member_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("team_member_profiles_management.id"), nullable=False
    )
    
    # Platform details
    platform_type: Mapped[PlatformType] = mapped_column(String(50), nullable=False)
    platform_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    platform_username: Mapped[Optional[str]] = mapped_column(String(255))
    platform_display_name: Mapped[Optional[str]] = mapped_column(String(255))
    platform_email: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Verification status
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    verification_method: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Integration metadata
    workspace_id: Mapped[Optional[str]] = mapped_column(String(255))  # Slack workspace, Teams tenant
    workspace_name: Mapped[Optional[str]] = mapped_column(String(255))
    additional_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    # Relationships
    team_member = relationship("TeamMemberProfileManagement", back_populates="platform_accounts")
    
    __table_args__ = (
        Index("idx_platform_account_team_member", "team_member_id"),
        Index("idx_platform_account_platform_user", "platform_type", "platform_user_id"),
        UniqueConstraint(
            "team_member_id", "platform_type", "platform_user_id",
            name="uq_team_member_platform_account"
        ),
    )


class TeamHierarchy(Base):
    """Team member hierarchical relationships and reporting structure"""
    
    __tablename__ = "team_hierarchy"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    
    # Relationship participants
    manager_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("team_member_profiles_management.id"), nullable=False
    )
    subordinate_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("team_member_profiles_management.id"), nullable=False
    )
    
    # Relationship type and context
    relationship_type: Mapped[HierarchyRelationType] = mapped_column(
        String(50), default=HierarchyRelationType.MANAGER
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False
    )
    
    # Relationship metadata
    percentage_reporting: Mapped[int] = mapped_column(Integer, default=100)  # % of time reporting
    is_primary_manager: Mapped[bool] = mapped_column(Boolean, default=True)
    effective_from: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    effective_until: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    # Relationships
    manager = relationship(
        "TeamMemberProfileManagement",
        foreign_keys=[manager_id],
        back_populates="subordinates"
    )
    subordinate = relationship(
        "TeamMemberProfileManagement",
        foreign_keys=[subordinate_id],
        back_populates="managers"
    )
    team = relationship("Team")
    
    __table_args__ = (
        Index("idx_team_hierarchy_manager", "manager_id"),
        Index("idx_team_hierarchy_subordinate", "subordinate_id"),
        Index("idx_team_hierarchy_team", "team_id"),
        Index("idx_team_hierarchy_active", "is_active"),
        UniqueConstraint(
            "manager_id", "subordinate_id", "relationship_type",
            name="uq_team_hierarchy_relationship"
        ),
    )


class TeamMemberStatusHistory(Base):
    """Track status changes for team members"""
    
    __tablename__ = "team_member_status_history"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    team_member_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("team_member_profiles_management.id"), nullable=False
    )
    
    # Status change details
    from_status: Mapped[Optional[MemberStatus]] = mapped_column(String(50))
    to_status: Mapped[MemberStatus] = mapped_column(String(50), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Change metadata
    changed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    change_source: Mapped[str] = mapped_column(String(50), default="manual")  # manual, system, integration
    
    # Timestamps
    effective_from: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    effective_until: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    team_member = relationship("TeamMemberProfileManagement")
    changed_by = relationship("User")
    
    __table_args__ = (
        Index("idx_status_history_team_member", "team_member_id"),
        Index("idx_status_history_effective", "effective_from", "effective_until"),
    )