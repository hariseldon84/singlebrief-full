"""Brief generation system models."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (JSON, Boolean, Column, DateTime, Float, ForeignKey,
                        Integer, String, Text)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base

class BriefStatus(str, Enum):
    """Brief generation status."""

    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BriefFormat(str, Enum):
    """Brief output format."""

    HTML = "html"
    TEXT = "text"
    PDF = "pdf"
    JSON = "json"

class BriefPriority(str, Enum):
    """Brief content priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class BriefTemplate(Base):
    """Brief template model for customizable brief layouts."""

    __tablename__ = "brief_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Template configuration
    template_data = Column(JSON, nullable=False)  # Jinja2 template structure
    sections = Column(JSON, nullable=False)  # Section configuration
    styling = Column(JSON)  # Visual styling preferences

    # Access control
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organization_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    is_default = Column(Boolean, default=False)
    is_shared = Column(Boolean, default=False)

    # Metadata
    version = Column(String(50), default="1.0.0")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    briefs = relationship("Brief", back_populates="template")
    user = relationship("User", back_populates="brief_templates")
    organization = relationship("Organization", back_populates="brief_templates")

class Brief(Base):
    """Main brief generation model."""

    __tablename__ = "briefs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)

    # Generation details
    status = Column(String(50), nullable=False, default=BriefStatus.PENDING)
    format = Column(String(50), nullable=False, default=BriefFormat.HTML)

    # Content
    content = Column(Text)  # Generated brief content
    summary = Column(Text)  # Brief summary/preview
    metadata = Column(JSON)  # Generation metadata, sources, etc.

    # Template and configuration
    template_id = Column(
        UUID(as_uuid=True), ForeignKey("brief_templates.id"), nullable=False
    )
    generation_config = Column(JSON)  # Generation-specific configuration

    # Ownership and scheduling
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organization_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    scheduled_for = Column(DateTime)  # When brief was scheduled to generate

    # Generation tracking
    generation_started_at = Column(DateTime)
    generation_completed_at = Column(DateTime)
    generation_duration_seconds = Column(Float)

    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    template = relationship("BriefTemplate", back_populates="briefs")
    user = relationship("User", back_populates="briefs")
    organization = relationship("Organization", back_populates="briefs")
    content_items = relationship(
        "BriefContentItem", back_populates="brief", cascade="all, delete-orphan"
    )
    deliveries = relationship(
        "BriefDelivery", back_populates="brief", cascade="all, delete-orphan"
    )
    analytics = relationship(
        "BriefAnalytics", back_populates="brief", cascade="all, delete-orphan"
    )

class BriefContentItem(Base):
    """Individual content items within a brief."""

    __tablename__ = "brief_content_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brief_id = Column(UUID(as_uuid=True), ForeignKey("briefs.id"), nullable=False)

    # Content details
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text)

    # Prioritization and scoring
    priority = Column(String(50), nullable=False, default=BriefPriority.MEDIUM)
    importance_score = Column(Float, default=0.5)  # 0.0 to 1.0
    urgency_score = Column(Float, default=0.5)  # 0.0 to 1.0
    relevance_score = Column(Float, default=0.5)  # 0.0 to 1.0

    # Source information
    source_type = Column(String(100))  # slack, email, github, etc.
    source_id = Column(String(255))  # Original source identifier
    source_url = Column(String(1000))  # Link to original content
    source_metadata = Column(JSON)  # Additional source details

    # Categorization
    category = Column(String(100))  # meetings, updates, issues, etc.
    tags = Column(JSON)  # Array of tags

    # Display configuration
    section = Column(String(100))  # Which template section this belongs to
    order_index = Column(Integer, default=0)  # Order within section
    is_featured = Column(Boolean, default=False)  # Highlight this item

    # Timestamps
    content_timestamp = Column(DateTime)  # When original content was created
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    brief = relationship("Brief", back_populates="content_items")

class BriefDelivery(Base):
    """Brief delivery tracking across multiple channels."""

    __tablename__ = "brief_deliveries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brief_id = Column(UUID(as_uuid=True), ForeignKey("briefs.id"), nullable=False)

    # Delivery details
    channel = Column(String(100), nullable=False)  # email, slack, dashboard, etc.
    status = Column(String(50), nullable=False, default="pending")
    format = Column(String(50), nullable=False)  # html, text, pdf

    # Delivery metadata
    recipient = Column(String(255))  # email address, slack channel, etc.
    delivery_config = Column(JSON)  # Channel-specific configuration

    # Tracking
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    opened_at = Column(DateTime)
    error_message = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    brief = relationship("Brief", back_populates="deliveries")

class BriefSchedule(Base):
    """Brief generation scheduling configuration."""

    __tablename__ = "brief_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Schedule configuration
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Timing
    cron_expression = Column(
        String(100), nullable=False
    )  # Cron expression for scheduling
    timezone = Column(String(100), default="UTC")
    is_active = Column(Boolean, default=True)

    # Generation configuration
    template_id = Column(
        UUID(as_uuid=True), ForeignKey("brief_templates.id"), nullable=False
    )
    generation_config = Column(JSON)  # Configuration for brief generation

    # Delivery configuration
    delivery_channels = Column(JSON)  # Array of delivery channel configurations

    # Ownership
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organization_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )

    # Execution tracking
    last_run_at = Column(DateTime)
    next_run_at = Column(DateTime)
    last_success_at = Column(DateTime)
    consecutive_failures = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    template = relationship("BriefTemplate")
    user = relationship("User", back_populates="brief_schedules")
    organization = relationship("Organization", back_populates="brief_schedules")

class BriefAnalytics(Base):
    """Brief analytics and engagement tracking."""

    __tablename__ = "brief_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brief_id = Column(UUID(as_uuid=True), ForeignKey("briefs.id"), nullable=False)

    # Engagement metrics
    views = Column(Integer, default=0)
    opens = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    time_spent_seconds = Column(Integer, default=0)

    # User feedback
    rating = Column(Integer)  # 1-5 rating
    feedback_text = Column(Text)
    is_useful = Column(Boolean)

    # Action tracking
    actions_taken = Column(JSON)  # Array of actions user took from brief
    links_clicked = Column(JSON)  # Array of links clicked

    # Performance metrics
    load_time_ms = Column(Integer)
    generation_time_ms = Column(Integer)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    brief = relationship("Brief", back_populates="analytics")
