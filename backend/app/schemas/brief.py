"""Pydantic schemas for brief-related API endpoints."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field

# Brief Template Schemas

class BriefTemplateBase(BaseModel):
    """Base schema for brief templates."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    template_data: Dict[str, Any] = Field(..., description="Jinja2 template structure")
    sections: Dict[str, Any] = Field(..., description="Section configuration")
    styling: Optional[Dict[str, Any]] = Field(
        None, description="Visual styling preferences"
    )

class BriefTemplateCreateRequest(BriefTemplateBase):
    """Schema for creating a new brief template."""

    is_default: bool = Field(False, description="Set as default template")
    is_shared: bool = Field(False, description="Share with team")

class BriefTemplateUpdateRequest(BriefTemplateBase):
    """Schema for updating a brief template."""

    pass

class BriefTemplateResponse(BriefTemplateBase):
    """Schema for brief template responses."""

    id: UUID
    user_id: UUID
    organization_id: UUID
    is_default: bool
    is_shared: bool
    version: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Brief Schemas

class BriefContentItemResponse(BaseModel):
    """Schema for brief content items."""

    id: UUID
    title: str
    content: str
    summary: Optional[str]
    priority: str
    importance_score: float
    urgency_score: float
    relevance_score: float
    source_type: Optional[str]
    source_url: Optional[str]
    category: Optional[str]
    tags: Optional[List[str]]
    section: str
    order_index: int
    is_featured: bool
    content_timestamp: Optional[datetime]

    class Config:
        from_attributes = True

class BriefResponse(BaseModel):
    """Schema for brief responses."""

    id: UUID
    title: str
    status: str
    format: str
    content: Optional[str]
    summary: Optional[str]
    metadata: Optional[Dict[str, Any]]
    template_id: UUID
    user_id: UUID
    organization_id: UUID
    scheduled_for: Optional[datetime]
    generation_started_at: Optional[datetime]
    generation_completed_at: Optional[datetime]
    generation_duration_seconds: Optional[float]
    error_message: Optional[str]
    retry_count: int
    created_at: datetime
    updated_at: datetime
    content_items: Optional[List[BriefContentItemResponse]] = None

    class Config:
        from_attributes = True

class BriefCreateRequest(BaseModel):
    """Schema for brief generation requests."""

    template_id: UUID
    config: Optional[Dict[str, Any]] = Field(
        None, description="Generation configuration"
    )
    async_generation: bool = Field(True, description="Generate asynchronously")
    scheduled_for: Optional[datetime] = Field(
        None, description="Schedule generation for specific time"
    )

# Brief Schedule Schemas

class BriefScheduleBase(BaseModel):
    """Base schema for brief schedules."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    cron_expression: str = Field(..., description="Cron expression for scheduling")
    timezone: str = Field("UTC", description="Timezone for scheduling")
    template_id: UUID
    generation_config: Optional[Dict[str, Any]] = Field(
        None, description="Generation configuration"
    )
    delivery_channels: Optional[List[Dict[str, Any]]] = Field(
        None, description="Delivery channel configurations"
    )

class BriefScheduleCreateRequest(BriefScheduleBase):
    """Schema for creating a brief schedule."""

    pass

class BriefScheduleUpdateRequest(BaseModel):
    """Schema for updating a brief schedule."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    cron_expression: Optional[str] = Field(
        None, description="Cron expression for scheduling"
    )
    timezone: Optional[str] = Field(None, description="Timezone for scheduling")
    generation_config: Optional[Dict[str, Any]] = Field(
        None, description="Generation configuration"
    )
    delivery_channels: Optional[List[Dict[str, Any]]] = Field(
        None, description="Delivery channel configurations"
    )
    is_active: Optional[bool] = Field(None, description="Active status")

class BriefScheduleResponse(BriefScheduleBase):
    """Schema for brief schedule responses."""

    id: UUID
    user_id: UUID
    organization_id: UUID
    is_active: bool
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    last_success_at: Optional[datetime]
    consecutive_failures: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Brief Preferences Schemas

class BriefPreferencesBase(BaseModel):
    """Base schema for brief preferences."""

    default_template_id: Optional[UUID] = Field(
        None, description="Default template for briefs"
    )
    time_range_hours: int = Field(
        24, ge=1, le=168, description="Default time range in hours"
    )
    max_items_per_section: int = Field(
        10, ge=1, le=50, description="Max items per section"
    )
    priority_threshold: float = Field(
        0.3, ge=0.0, le=1.0, description="Minimum priority threshold"
    )
    include_sources: Optional[List[str]] = Field(
        None, description="Preferred data sources"
    )
    exclude_sources: Optional[List[str]] = Field(
        None, description="Excluded data sources"
    )
    preferred_sections: Optional[List[str]] = Field(
        None, description="Preferred brief sections"
    )
    notification_preferences: Optional[Dict[str, Any]] = Field(
        None, description="Notification settings"
    )
    delivery_preferences: Optional[Dict[str, Any]] = Field(
        None, description="Delivery settings"
    )

class BriefPreferencesCreateRequest(BriefPreferencesBase):
    """Schema for creating brief preferences."""

    pass

class BriefPreferencesUpdateRequest(BriefPreferencesBase):
    """Schema for updating brief preferences."""

    pass

class BriefPreferencesResponse(BriefPreferencesBase):
    """Schema for brief preferences responses."""

    id: UUID
    user_id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Template Section Schemas

class TemplateSectionBase(BaseModel):
    """Base schema for template sections."""

    name: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    order_index: int = Field(0, ge=0, description="Display order")
    is_enabled: bool = Field(True, description="Whether section is enabled")
    configuration: Optional[Dict[str, Any]] = Field(
        None, description="Section-specific configuration"
    )

class TemplateSectionResponse(TemplateSectionBase):
    """Schema for template section responses."""

    id: UUID
    template_id: UUID

    class Config:
        from_attributes = True

# Brief Analytics Schemas

class BriefAnalyticsResponse(BaseModel):
    """Schema for brief analytics responses."""

    id: UUID
    brief_id: UUID
    views: int
    opens: int
    clicks: int
    time_spent_seconds: int
    rating: Optional[int]
    feedback_text: Optional[str]
    is_useful: Optional[bool]
    actions_taken: Optional[List[str]]
    links_clicked: Optional[List[str]]
    load_time_ms: Optional[int]
    generation_time_ms: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BriefFeedbackRequest(BaseModel):
    """Schema for brief feedback submission."""

    rating: Optional[int] = Field(None, ge=1, le=5, description="Brief rating (1-5)")
    feedback_text: Optional[str] = Field(
        None, max_length=1000, description="Feedback text"
    )
    is_useful: Optional[bool] = Field(None, description="Whether brief was useful")
    actions_taken: Optional[List[str]] = Field(
        None, description="Actions taken from brief"
    )

# Delivery Schemas

class BriefDeliveryBase(BaseModel):
    """Base schema for brief deliveries."""

    channel: str = Field(
        ..., description="Delivery channel (email, slack, dashboard, etc.)"
    )
    format: str = Field(..., description="Content format (html, text, pdf)")
    recipient: str = Field(..., description="Delivery recipient")
    delivery_config: Optional[Dict[str, Any]] = Field(
        None, description="Channel-specific configuration"
    )

class BriefDeliveryResponse(BriefDeliveryBase):
    """Schema for brief delivery responses."""

    id: UUID
    brief_id: UUID
    status: str
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    opened_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Template Marketplace Schemas

class TemplateMarketplaceItem(BaseModel):
    """Schema for template marketplace items."""

    id: UUID
    name: str
    description: str
    author: str
    category: str
    tags: List[str]
    download_count: int
    rating: float
    preview_url: Optional[str]
    is_featured: bool
    created_at: datetime

class TemplateMarketplaceResponse(BaseModel):
    """Schema for template marketplace responses."""

    items: List[TemplateMarketplaceItem]
    total_count: int
    page: int
    page_size: int

# Validation Schemas

class TemplateValidationRequest(BaseModel):
    """Schema for template validation requests."""

    template_data: Dict[str, Any] = Field(..., description="Template data to validate")

class TemplateValidationResponse(BaseModel):
    """Schema for template validation responses."""

    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]

# Export/Import Schemas

class TemplateExportResponse(BaseModel):
    """Schema for template export responses."""

    template: BriefTemplateResponse
    export_format: str
    export_data: Dict[str, Any]
    created_at: datetime

class TemplateImportRequest(BaseModel):
    """Schema for template import requests."""

    import_data: Dict[str, Any] = Field(..., description="Template import data")
    import_format: str = Field(..., description="Import format")
    overwrite_existing: bool = Field(False, description="Overwrite if template exists")

class TemplateImportResponse(BaseModel):
    """Schema for template import responses."""

    success: bool
    template: Optional[BriefTemplateResponse]
    errors: List[str]
    warnings: List[str]
