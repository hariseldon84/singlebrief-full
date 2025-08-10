"""
Pydantic schemas for Team Management API

Schemas for team member profile management, roles, designations, and expertise tags.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class MemberStatusEnum(str, Enum):
    """Team member status options"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"
    PENDING_INVITATION = "pending_invitation"
    SUSPENDED = "suspended"


class ContactPreferenceEnum(str, Enum):
    """Contact method preferences"""
    IN_APP = "in_app"
    EMAIL = "email"
    SLACK = "slack"
    TEAMS = "teams"
    DISABLED = "disabled"


class PlatformTypeEnum(str, Enum):
    """External platform types for integration"""
    SLACK = "slack"
    MICROSOFT_TEAMS = "teams"
    EMAIL = "email"
    GOOGLE_WORKSPACE = "google_workspace"


class HierarchyRelationTypeEnum(str, Enum):
    """Types of hierarchical relationships"""
    MANAGER = "manager"
    DIRECT_REPORT = "direct_report"
    TEAM_LEAD = "team_lead"
    PEER = "peer"
    COLLABORATOR = "collaborator"


# Base schemas for taxonomy items
class RoleTaxonomyBase(BaseModel):
    name: str = Field(..., max_length=100)
    display_name: str = Field(..., max_length=150)
    description: Optional[str] = None
    category: str = Field(..., max_length=50)
    seniority_level: Optional[str] = Field(None, max_length=50)
    is_system_role: bool = False
    default_permissions: Dict[str, Any] = Field(default_factory=dict)
    suggested_tags: List[str] = Field(default_factory=list)
    is_active: bool = True


class RoleTaxonomyCreate(RoleTaxonomyBase):
    pass


class RoleTaxonomyUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    display_name: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    seniority_level: Optional[str] = Field(None, max_length=50)
    default_permissions: Optional[Dict[str, Any]] = None
    suggested_tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class RoleTaxonomyResponse(RoleTaxonomyBase):
    id: str
    organization_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DesignationTaxonomyBase(BaseModel):
    name: str = Field(..., max_length=100)
    display_name: str = Field(..., max_length=150)
    description: Optional[str] = None
    hierarchy_level: int = 0
    department: Optional[str] = Field(None, max_length=100)
    is_system_designation: bool = False
    is_active: bool = True


class DesignationTaxonomyCreate(DesignationTaxonomyBase):
    pass


class DesignationTaxonomyUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    display_name: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = None
    hierarchy_level: Optional[int] = None
    department: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class DesignationTaxonomyResponse(DesignationTaxonomyBase):
    id: str
    organization_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExpertiseTagBase(BaseModel):
    name: str = Field(..., max_length=100)
    display_name: str = Field(..., max_length=150)
    description: Optional[str] = None
    category: str = Field(..., max_length=50)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")  # hex color
    is_system_tag: bool = False
    is_active: bool = True


class ExpertiseTagCreate(ExpertiseTagBase):
    pass


class ExpertiseTagUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    display_name: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    is_active: Optional[bool] = None


class ExpertiseTagResponse(ExpertiseTagBase):
    id: str
    organization_id: Optional[str]
    usage_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Platform Account schemas
class PlatformAccountBase(BaseModel):
    platform_type: PlatformTypeEnum
    platform_user_id: str = Field(..., max_length=255)
    platform_username: Optional[str] = Field(None, max_length=255)
    platform_display_name: Optional[str] = Field(None, max_length=255)
    platform_email: Optional[str] = Field(None, max_length=255)
    workspace_id: Optional[str] = Field(None, max_length=255)
    workspace_name: Optional[str] = Field(None, max_length=255)
    additional_metadata: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class PlatformAccountCreate(PlatformAccountBase):
    pass


class PlatformAccountUpdate(BaseModel):
    platform_username: Optional[str] = Field(None, max_length=255)
    platform_display_name: Optional[str] = Field(None, max_length=255)
    platform_email: Optional[str] = Field(None, max_length=255)
    workspace_id: Optional[str] = Field(None, max_length=255)
    workspace_name: Optional[str] = Field(None, max_length=255)
    additional_metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class PlatformAccountResponse(PlatformAccountBase):
    id: str
    is_verified: bool
    verified_at: Optional[datetime]
    verification_method: Optional[str]
    last_sync_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Team Hierarchy schemas
class TeamHierarchyBase(BaseModel):
    relationship_type: HierarchyRelationTypeEnum = HierarchyRelationTypeEnum.MANAGER
    percentage_reporting: int = Field(100, ge=0, le=100)
    is_primary_manager: bool = True
    effective_from: datetime = Field(default_factory=datetime.utcnow)
    effective_until: Optional[datetime] = None
    is_active: bool = True


class TeamHierarchyCreate(TeamHierarchyBase):
    manager_id: str
    subordinate_id: str
    team_id: str


class TeamHierarchyUpdate(BaseModel):
    relationship_type: Optional[HierarchyRelationTypeEnum] = None
    percentage_reporting: Optional[int] = Field(None, ge=0, le=100)
    is_primary_manager: Optional[bool] = None
    effective_until: Optional[datetime] = None
    is_active: Optional[bool] = None


class TeamHierarchyResponse(TeamHierarchyBase):
    id: str
    manager_id: str
    subordinate_id: str
    team_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Expertise tag assignment schema
class ExpertiseTagAssignment(BaseModel):
    tag_id: str
    tag_name: Optional[str] = None  # For user-defined tags
    proficiency_level: int = Field(3, ge=1, le=5)  # 1-5 scale


# Main Team Member Profile schemas
class TeamMemberProfileBase(BaseModel):
    # Role and designation
    custom_role: Optional[str] = Field(None, max_length=150)
    custom_designation: Optional[str] = Field(None, max_length=150)
    
    # Profile information
    profile_photo_url: Optional[str] = Field(None, max_length=500)
    bio: Optional[str] = None
    location: Optional[str] = Field(None, max_length=200)
    timezone: Optional[str] = Field(None, max_length=50)
    
    # Contact information
    work_phone: Optional[str] = Field(None, max_length=50)
    mobile_phone: Optional[str] = Field(None, max_length=50)
    secondary_email: Optional[str] = Field(None, max_length=255)
    
    # Status and availability
    status: MemberStatusEnum = MemberStatusEnum.ACTIVE
    availability_status: Optional[str] = Field(None, max_length=100)
    
    # Workload and capacity
    current_workload: float = Field(0.5, ge=0.0, le=1.0)
    capacity_percentage: int = Field(100, ge=0, le=100)
    
    # Expertise and skills
    skills_summary: Optional[str] = None
    years_experience: Optional[int] = Field(None, ge=0)
    
    # Contact preferences
    query_contact_preference: ContactPreferenceEnum = ContactPreferenceEnum.IN_APP
    urgent_contact_preference: ContactPreferenceEnum = ContactPreferenceEnum.EMAIL
    notification_preference: ContactPreferenceEnum = ContactPreferenceEnum.EMAIL
    
    # Communication settings
    response_time_expectation_hours: int = Field(24, ge=1, le=168)  # Max 1 week
    working_hours_start: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    working_hours_end: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    working_days: List[str] = Field(default_factory=list)
    
    # Admin fields
    notes: Optional[str] = None
    
    @field_validator('working_days')
    @classmethod
    def validate_working_days(cls, v):
        valid_days = {'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'}
        if v is not None:
            for day in v:
                if day.lower() not in valid_days:
                    raise ValueError(f'Invalid working day: {day}')
        return v


class TeamMemberProfileCreate(TeamMemberProfileBase):
    name: str = Field(..., max_length=200, description="Full name of the team member")
    email: str = Field(..., max_length=255, description="Email address of the team member")
    role: str = Field(..., max_length=150, description="Role of the team member (freeform text)")
    team_id: str
    # Optional fields - keeping for backward compatibility but making them optional
    user_id: Optional[str] = None
    role_id: Optional[str] = None
    designation_id: Optional[str] = None
    expertise_tags: List[ExpertiseTagAssignment] = Field(default_factory=list)
    platform_accounts: List[PlatformAccountCreate] = Field(default_factory=list)


class TeamMemberProfileUpdate(BaseModel):
    # Role and designation
    role_id: Optional[str] = None
    designation_id: Optional[str] = None
    custom_role: Optional[str] = Field(None, max_length=150)
    custom_designation: Optional[str] = Field(None, max_length=150)
    
    # Profile information
    profile_photo_url: Optional[str] = Field(None, max_length=500)
    bio: Optional[str] = None
    location: Optional[str] = Field(None, max_length=200)
    timezone: Optional[str] = Field(None, max_length=50)
    
    # Contact information
    work_phone: Optional[str] = Field(None, max_length=50)
    mobile_phone: Optional[str] = Field(None, max_length=50)
    secondary_email: Optional[str] = Field(None, max_length=255)
    
    # Status and availability
    status: Optional[MemberStatusEnum] = None
    availability_status: Optional[str] = Field(None, max_length=100)
    
    # Workload and capacity
    current_workload: Optional[float] = Field(None, ge=0.0, le=1.0)
    capacity_percentage: Optional[int] = Field(None, ge=0, le=100)
    
    # Expertise and skills
    skills_summary: Optional[str] = None
    years_experience: Optional[int] = Field(None, ge=0)
    
    # Contact preferences
    query_contact_preference: Optional[ContactPreferenceEnum] = None
    urgent_contact_preference: Optional[ContactPreferenceEnum] = None
    notification_preference: Optional[ContactPreferenceEnum] = None
    
    # Communication settings
    response_time_expectation_hours: Optional[int] = Field(None, ge=1, le=168)
    working_hours_start: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    working_hours_end: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    working_days: Optional[List[str]] = None
    
    # Admin fields
    notes: Optional[str] = None
    
    # Expertise tags (replace all)
    expertise_tags: Optional[List[ExpertiseTagAssignment]] = None


class TeamMemberProfileResponse(TeamMemberProfileBase):
    id: str
    user_id: str
    team_id: str
    organization_id: str
    role_id: Optional[str]
    designation_id: Optional[str]
    
    # Verification status
    slack_verified: bool
    teams_verified: bool
    email_verified: bool
    
    # Performance metrics
    total_queries_received: int
    total_queries_responded: int
    average_response_time_hours: float
    response_quality_score: float
    
    # Timestamps
    invitation_sent_at: Optional[datetime]
    invitation_accepted_at: Optional[datetime]
    onboarded_at: Optional[datetime]
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    
    # Related data
    role: Optional[RoleTaxonomyResponse] = None
    designation: Optional[DesignationTaxonomyResponse] = None
    expertise_tags: List[ExpertiseTagResponse] = Field(default_factory=list)
    platform_accounts: List[PlatformAccountResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


# Bulk operations schemas
class TeamMemberBulkCreate(BaseModel):
    team_members: List[TeamMemberProfileCreate]


class TeamMemberImportCSV(BaseModel):
    csv_data: str  # Base64 encoded CSV data
    team_id: str
    skip_header: bool = True
    column_mapping: Dict[str, str] = Field(default_factory=dict)  # CSV column -> field mapping


class BulkOperationResponse(BaseModel):
    total_records: int
    successful: int
    failed: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    created_ids: List[str] = Field(default_factory=list)


# Search and filtering schemas
class TeamMemberSearchRequest(BaseModel):
    # Text search
    search_query: Optional[str] = None  # Full-text search across profiles
    
    # Filters
    team_ids: Optional[List[str]] = None
    role_ids: Optional[List[str]] = None
    designation_ids: Optional[List[str]] = None
    expertise_tag_ids: Optional[List[str]] = None
    statuses: Optional[List[MemberStatusEnum]] = None
    
    # Workload and availability filters
    min_capacity: Optional[int] = Field(None, ge=0, le=100)
    max_capacity: Optional[int] = Field(None, ge=0, le=100)
    min_workload: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_workload: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # Platform verification filters
    slack_verified: Optional[bool] = None
    teams_verified: Optional[bool] = None
    email_verified: Optional[bool] = None
    
    # Date filters
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    
    # Pagination
    skip: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=100)
    
    # Sorting
    sort_by: Optional[str] = Field("created_at", pattern="^(name|created_at|updated_at|response_quality_score|average_response_time_hours)$")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$")


class TeamMemberSearchResponse(BaseModel):
    total: int
    skip: int
    limit: int
    results: List[TeamMemberProfileResponse]


# Status history schema
class StatusChangeCreate(BaseModel):
    to_status: MemberStatusEnum
    reason: Optional[str] = None
    notes: Optional[str] = None
    effective_from: datetime = Field(default_factory=datetime.utcnow)


class StatusHistoryResponse(BaseModel):
    id: str
    from_status: Optional[MemberStatusEnum]
    to_status: MemberStatusEnum
    reason: Optional[str]
    notes: Optional[str]
    changed_by_user_id: Optional[str]
    change_source: str
    effective_from: datetime
    effective_until: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


