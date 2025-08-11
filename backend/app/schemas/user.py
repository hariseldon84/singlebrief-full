"""
User and organization API schemas
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr

from app.models.user import ConsentType, UserRole

class UserResponse(BaseModel):
    """User response schema"""

    id: str
    email: EmailStr
    full_name: str
    avatar_url: Optional[str]
    role: UserRole
    is_active: bool
    is_verified: bool
    is_2fa_enabled: bool
    last_login: Optional[datetime]
    created_at: datetime
    organization_id: Optional[str]

    class Config:
        from_attributes = True

class UserProfile(BaseModel):
    """Extended user profile"""

    id: str
    email: EmailStr
    full_name: str
    avatar_url: Optional[str]
    role: UserRole
    is_active: bool
    is_verified: bool
    is_2fa_enabled: bool
    last_login: Optional[datetime]
    login_count: int
    privacy_settings: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]
    organization: Optional["OrganizationResponse"]
    teams: List["TeamResponse"] = []

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    """User update schema"""

    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    privacy_settings: Optional[Dict[str, Any]] = None

class OrganizationResponse(BaseModel):
    """Organization response schema"""

    id: str
    name: str
    slug: str
    domain: Optional[str]
    is_active: bool
    privacy_policy_version: str
    data_retention_days: int
    created_at: datetime

    class Config:
        from_attributes = True

class OrganizationCreate(BaseModel):
    """Organization creation schema"""

    name: str
    slug: Optional[str] = None
    domain: Optional[str] = None

class OrganizationUpdate(BaseModel):
    """Organization update schema"""

    name: Optional[str] = None
    domain: Optional[str] = None
    data_retention_days: Optional[int] = None

class TeamResponse(BaseModel):
    """Team response schema"""

    id: str
    name: str
    description: Optional[str]
    organization_id: str
    is_public: bool
    is_active: bool
    created_at: datetime
    member_count: Optional[int] = 0

    class Config:
        from_attributes = True

class TeamCreate(BaseModel):
    """Team creation schema"""

    name: str
    description: Optional[str] = None
    is_public: bool = False

class TeamUpdate(BaseModel):
    """Team update schema"""

    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None

class TeamMemberResponse(BaseModel):
    """Team member response"""

    user: UserResponse
    role: UserRole
    joined_at: datetime
    is_active: bool

class TeamInvite(BaseModel):
    """Team invitation schema"""

    email: EmailStr
    role: UserRole = UserRole.TEAM_MEMBER
    message: Optional[str] = None

class UserConsentResponse(BaseModel):
    """User consent response"""

    id: str
    consent_type: ConsentType
    is_granted: bool
    version: str
    purpose: Optional[str]
    granted_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True

class UserConsentUpdate(BaseModel):
    """User consent update"""

    consent_type: ConsentType
    is_granted: bool
    purpose: Optional[str] = None

class PrivacySettings(BaseModel):
    """Privacy settings schema"""

    data_collection: bool = True
    memory_storage: bool = True
    team_sharing: bool = True
    analytics: bool = False
    marketing: bool = False

    # Data retention preferences
    auto_delete_data: bool = False
    data_retention_days: Optional[int] = None

    # Sharing preferences
    share_activity_status: bool = True
    share_response_times: bool = False
    visible_to_organization: bool = True

class UserSessionResponse(BaseModel):
    """User session response"""

    id: str
    device_info: Optional[str]
    ip_address: str
    user_agent: Optional[str]
    last_activity: datetime
    created_at: datetime
    is_current: bool = False

    class Config:
        from_attributes = True

# Forward reference resolution
UserProfile.model_rebuild()
TeamResponse.model_rebuild()
