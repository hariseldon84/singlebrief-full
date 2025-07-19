"""Intelligence generation database models for SingleBrief.

This module contains all database models related to brief generation,
query processing, AI responses, and intelligence delivery.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, JSON, Float,
    ForeignKey, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Query(Base):
    """User queries and requests for intelligence.
    
    Tracks all queries made by users, whether they're ad-hoc questions
    or structured brief requests.
    """
    __tablename__ = "queries"

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
    conversation_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Query identification
    query_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Type: ad_hoc, daily_brief, team_update, project_status, custom_brief"
    )
    priority: Mapped[str] = mapped_column(
        String(20), 
        default="medium",
        comment="Priority: low, medium, high, urgent"
    )
    
    # Query content
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    query_intent: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="Detected intent: information_request, status_update, decision_support, etc."
    )
    query_context: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="Context and parameters for the query"
    )
    
    # Scope and filtering
    scope: Mapped[str] = mapped_column(
        String(20), 
        default="team",
        comment="Scope: personal, team, organization, specific_sources"
    )
    time_range_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    time_range_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    data_sources: Mapped[Optional[List[str]]] = mapped_column(
        JSONB,
        comment="Specific data sources to include"
    )
    
    # Processing status
    status: Mapped[str] = mapped_column(
        String(20), 
        default="pending",
        comment="Status: pending, processing, completed, failed, cancelled"
    )
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    processing_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    processing_duration_ms: Mapped[Optional[int]] = mapped_column()
    
    # Result metadata
    response_count: Mapped[int] = mapped_column(default=0)
    sources_used: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSONB,
        comment="Sources and integrations used to answer the query"
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(
        comment="Overall confidence in the response 0.0-1.0"
    )
    
    # User feedback
    user_rating: Mapped[Optional[int]] = mapped_column(
        comment="User rating 1-5 stars"
    )
    user_feedback: Mapped[Optional[str]] = mapped_column(Text)
    feedback_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(default=0)
    
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
    user: Mapped["User"] = relationship("User", back_populates="queries")
    organization: Mapped["Organization"] = relationship("Organization", back_populates="queries")
    conversation: Mapped[Optional["Conversation"]] = relationship("Conversation")
    briefs: Mapped[List["Brief"]] = relationship(
        "Brief", 
        back_populates="query",
        cascade="all, delete-orphan"
    )
    ai_responses: Mapped[List["AIResponse"]] = relationship(
        "AIResponse", 
        back_populates="query",
        cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        Index("idx_queries_user_created", "user_id", "created_at"),
        Index("idx_queries_org_created", "organization_id", "created_at"),
        Index("idx_queries_type", "query_type"),
        Index("idx_queries_status", "status"),
        Index("idx_queries_priority", "priority"),
        Index("idx_queries_rating", "user_rating"),
        CheckConstraint(
            "query_type IN ('ad_hoc', 'daily_brief', 'team_update', 'project_status', 'custom_brief', 'team_interrogation')",
            name="check_query_type"
        ),
        CheckConstraint(
            "priority IN ('low', 'medium', 'high', 'urgent')",
            name="check_query_priority"
        ),
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')",
            name="check_query_status"
        ),
        CheckConstraint(
            "scope IN ('personal', 'team', 'organization', 'specific_sources')",
            name="check_query_scope"
        ),
        CheckConstraint(
            "confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)",
            name="check_query_confidence_range"
        ),
        CheckConstraint(
            "user_rating IS NULL OR (user_rating >= 1 AND user_rating <= 5)",
            name="check_user_rating_range"
        ),
    )

    def __repr__(self) -> str:
        return f"<Query(id={self.id}, type={self.query_type}, status={self.status})>"


class Brief(Base):
    """Generated intelligence briefs and reports.
    
    Stores the generated briefs, daily updates, and intelligence reports
    delivered to users.
    """
    __tablename__ = "briefs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    query_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("queries.id", ondelete="CASCADE"),
        nullable=False
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
    
    # Brief identification
    brief_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Type: daily_brief, weekly_summary, project_update, ad_hoc_report"
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    template_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="Template used to generate this brief"
    )
    
    # Content
    executive_summary: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_format: Mapped[str] = mapped_column(
        String(20), 
        default="markdown",
        comment="Format: markdown, html, plain_text, json"
    )
    
    # Content structure
    sections: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        comment="Structured sections of the brief"
    )
    key_insights: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        comment="Key insights and takeaways"
    )
    action_items: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSONB,
        comment="Recommended actions and next steps"
    )
    
    # Metadata and quality
    word_count: Mapped[int] = mapped_column(default=0)
    reading_time_minutes: Mapped[int] = mapped_column(default=0)
    complexity_score: Mapped[float] = mapped_column(
        default=0.5,
        comment="Content complexity score 0.0-1.0"
    )
    
    # Sources and trust
    source_count: Mapped[int] = mapped_column(default=0)
    sources: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        comment="Sources used to generate the brief"
    )
    confidence_score: Mapped[float] = mapped_column(
        default=0.5,
        comment="Overall confidence in the brief 0.0-1.0"
    )
    trust_indicators: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="Trust and verification indicators"
    )
    
    # Generation metadata
    ai_model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    generation_method: Mapped[str] = mapped_column(
        String(50), 
        default="rag",
        comment="Method: rag, synthesis, template, hybrid"
    )
    generation_time_ms: Mapped[int] = mapped_column(default=0)
    token_usage: Mapped[Optional[Dict[str, int]]] = mapped_column(
        JSONB,
        comment="Token usage statistics"
    )
    
    # Delivery status
    delivery_status: Mapped[str] = mapped_column(
        String(20), 
        default="pending",
        comment="Status: pending, delivered, failed, cancelled"
    )
    delivery_channels: Mapped[List[str]] = mapped_column(
        JSONB,
        default=list,
        comment="Channels used for delivery: web, email, slack, teams"
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # User interaction
    viewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    view_count: Mapped[int] = mapped_column(default=0)
    time_spent_reading_seconds: Mapped[Optional[int]] = mapped_column()
    
    # User feedback
    user_rating: Mapped[Optional[int]] = mapped_column(
        comment="User rating 1-5 stars"
    )
    user_feedback: Mapped[Optional[str]] = mapped_column(Text)
    feedback_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Archival and retention
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
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
    query: Mapped["Query"] = relationship("Query", back_populates="briefs")
    user: Mapped["User"] = relationship("User", back_populates="briefs")
    organization: Mapped["Organization"] = relationship("Organization", back_populates="briefs")
    delivery_logs: Mapped[List["BriefDeliveryLog"]] = relationship(
        "BriefDeliveryLog", 
        back_populates="brief",
        cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        Index("idx_briefs_user_created", "user_id", "created_at"),
        Index("idx_briefs_org_created", "organization_id", "created_at"),
        Index("idx_briefs_type", "brief_type"),
        Index("idx_briefs_delivery_status", "delivery_status"),
        Index("idx_briefs_rating", "user_rating"),
        Index("idx_briefs_confidence", "confidence_score"),
        Index("idx_briefs_viewed", "viewed_at"),
        CheckConstraint(
            "brief_type IN ('daily_brief', 'weekly_summary', 'project_update', 'ad_hoc_report', 'team_update')",
            name="check_brief_type"
        ),
        CheckConstraint(
            "content_format IN ('markdown', 'html', 'plain_text', 'json')",
            name="check_content_format"
        ),
        CheckConstraint(
            "generation_method IN ('rag', 'synthesis', 'template', 'hybrid')",
            name="check_generation_method"
        ),
        CheckConstraint(
            "delivery_status IN ('pending', 'delivered', 'failed', 'cancelled')",
            name="check_delivery_status"
        ),
        CheckConstraint(
            "confidence_score >= 0.0 AND confidence_score <= 1.0",
            name="check_brief_confidence_range"
        ),
        CheckConstraint(
            "complexity_score >= 0.0 AND complexity_score <= 1.0",
            name="check_complexity_score_range"
        ),
        CheckConstraint(
            "user_rating IS NULL OR (user_rating >= 1 AND user_rating <= 5)",
            name="check_brief_rating_range"
        ),
    )

    def __repr__(self) -> str:
        return f"<Brief(id={self.id}, title='{self.title}', type={self.brief_type})>"


class AIResponse(Base):
    """AI model responses and generation metadata.
    
    Tracks individual AI responses, including multiple attempts,
    model performance, and response quality metrics.
    """
    __tablename__ = "ai_responses"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    query_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("queries.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Response identification
    response_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Type: initial_response, refinement, follow_up, error_recovery"
    )
    attempt_number: Mapped[int] = mapped_column(
        default=1,
        comment="Attempt number for this response"
    )
    
    # AI model details
    ai_model: Mapped[str] = mapped_column(String(100), nullable=False)
    ai_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model_version: Mapped[Optional[str]] = mapped_column(String(50))
    temperature: Mapped[Optional[float]] = mapped_column()
    max_tokens: Mapped[Optional[int]] = mapped_column()
    
    # Response content
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    response_format: Mapped[str] = mapped_column(
        String(20), 
        default="text",
        comment="Format: text, json, markdown, structured"
    )
    
    # Processing details
    prompt_tokens: Mapped[int] = mapped_column(default=0)
    completion_tokens: Mapped[int] = mapped_column(default=0)
    total_tokens: Mapped[int] = mapped_column(default=0)
    processing_time_ms: Mapped[int] = mapped_column(default=0)
    
    # Quality metrics
    confidence_score: Mapped[float] = mapped_column(
        default=0.5,
        comment="Model confidence in response 0.0-1.0"
    )
    relevance_score: Mapped[Optional[float]] = mapped_column(
        comment="Relevance to query 0.0-1.0"
    )
    coherence_score: Mapped[Optional[float]] = mapped_column(
        comment="Response coherence 0.0-1.0"
    )
    completeness_score: Mapped[Optional[float]] = mapped_column(
        comment="Response completeness 0.0-1.0"
    )
    
    # Context and sources
    context_used: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSONB,
        comment="Context and sources used for generation"
    )
    retrieval_results: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSONB,
        comment="RAG retrieval results and scores"
    )
    
    # Response status
    status: Mapped[str] = mapped_column(
        String(20), 
        default="completed",
        comment="Status: completed, failed, timeout, cancelled"
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    error_type: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Selection and usage
    is_selected: Mapped[bool] = mapped_column(
        Boolean, 
        default=False,
        comment="Whether this response was selected for the final brief"
    )
    selection_reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # Cost tracking
    estimated_cost: Mapped[Optional[float]] = mapped_column(
        comment="Estimated cost for this response"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )

    # Relationships
    query: Mapped["Query"] = relationship("Query", back_populates="ai_responses")

    # Constraints
    __table_args__ = (
        Index("idx_ai_responses_query_created", "query_id", "created_at"),
        Index("idx_ai_responses_model", "ai_model"),
        Index("idx_ai_responses_status", "status"),
        Index("idx_ai_responses_selected", "is_selected"),
        Index("idx_ai_responses_confidence", "confidence_score"),
        Index("idx_ai_responses_attempt", "attempt_number"),
        CheckConstraint(
            "response_type IN ('initial_response', 'refinement', 'follow_up', 'error_recovery')",
            name="check_response_type"
        ),
        CheckConstraint(
            "response_format IN ('text', 'json', 'markdown', 'structured')",
            name="check_response_format"
        ),
        CheckConstraint(
            "status IN ('completed', 'failed', 'timeout', 'cancelled')",
            name="check_ai_response_status"
        ),
        CheckConstraint(
            "confidence_score >= 0.0 AND confidence_score <= 1.0",
            name="check_ai_confidence_range"
        ),
        CheckConstraint(
            "relevance_score IS NULL OR (relevance_score >= 0.0 AND relevance_score <= 1.0)",
            name="check_relevance_score_range"
        ),
        CheckConstraint(
            "coherence_score IS NULL OR (coherence_score >= 0.0 AND coherence_score <= 1.0)",
            name="check_coherence_score_range"
        ),
        CheckConstraint(
            "completeness_score IS NULL OR (completeness_score >= 0.0 AND completeness_score <= 1.0)",
            name="check_completeness_score_range"
        ),
        CheckConstraint(
            "temperature IS NULL OR (temperature >= 0.0 AND temperature <= 2.0)",
            name="check_temperature_range"
        ),
    )

    def __repr__(self) -> str:
        return f"<AIResponse(id={self.id}, model={self.ai_model}, status={self.status})>"


class BriefDeliveryLog(Base):
    """Delivery logs for briefs across different channels.
    
    Tracks how briefs are delivered to users across various channels
    and their delivery success/failure status.
    """
    __tablename__ = "brief_delivery_logs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    brief_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("briefs.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Delivery details
    delivery_channel: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Channel: web, email, slack, teams, webhook, api"
    )
    delivery_method: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Method: push, pull, notification, direct_message"
    )
    
    # Recipient information
    recipient_type: Mapped[str] = mapped_column(
        String(20), 
        default="user",
        comment="Type: user, team, webhook, external_system"
    )
    recipient_id: Mapped[str] = mapped_column(
        String(255), 
        nullable=False,
        comment="ID of recipient (user_id, email, webhook_url, etc.)"
    )
    recipient_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="Additional recipient metadata"
    )
    
    # Delivery status
    status: Mapped[str] = mapped_column(
        String(20), 
        default="pending",
        comment="Status: pending, sent, delivered, failed, bounced, rejected"
    )
    attempt_number: Mapped[int] = mapped_column(default=1)
    max_attempts: Mapped[int] = mapped_column(default=3)
    
    # Content delivered
    content_type: Mapped[str] = mapped_column(
        String(20), 
        default="full",
        comment="Content type: full, summary, notification, link_only"
    )
    content_size_bytes: Mapped[Optional[int]] = mapped_column()
    
    # Delivery timing
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    delivery_duration_ms: Mapped[Optional[int]] = mapped_column()
    
    # External tracking
    external_message_id: Mapped[Optional[str]] = mapped_column(String(255))
    external_tracking_id: Mapped[Optional[str]] = mapped_column(String(255))
    external_status: Mapped[Optional[str]] = mapped_column(String(50))
    
    # User engagement
    opened_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    clicked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    engagement_score: Mapped[Optional[float]] = mapped_column(
        comment="Engagement score 0.0-1.0"
    )
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    error_code: Mapped[Optional[str]] = mapped_column(String(50))
    retry_after: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Metadata
    delivery_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="Channel-specific delivery metadata"
    )
    
    # Timestamp
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
    brief: Mapped["Brief"] = relationship("Brief", back_populates="delivery_logs")

    # Constraints
    __table_args__ = (
        Index("idx_brief_delivery_logs_brief", "brief_id"),
        Index("idx_brief_delivery_logs_channel", "delivery_channel"),
        Index("idx_brief_delivery_logs_status", "status"),
        Index("idx_brief_delivery_logs_recipient", "recipient_id"),
        Index("idx_brief_delivery_logs_scheduled", "scheduled_at"),
        Index("idx_brief_delivery_logs_delivered", "delivered_at"),
        CheckConstraint(
            "delivery_channel IN ('web', 'email', 'slack', 'teams', 'webhook', 'api', 'sms')",
            name="check_delivery_channel"
        ),
        CheckConstraint(
            "delivery_method IN ('push', 'pull', 'notification', 'direct_message', 'broadcast')",
            name="check_delivery_method"
        ),
        CheckConstraint(
            "recipient_type IN ('user', 'team', 'webhook', 'external_system')",
            name="check_recipient_type"
        ),
        CheckConstraint(
            "status IN ('pending', 'sent', 'delivered', 'failed', 'bounced', 'rejected')",
            name="check_delivery_status"
        ),
        CheckConstraint(
            "content_type IN ('full', 'summary', 'notification', 'link_only')",
            name="check_content_type"
        ),
        CheckConstraint(
            "engagement_score IS NULL OR (engagement_score >= 0.0 AND engagement_score <= 1.0)",
            name="check_engagement_score_range"
        ),
    )

    def __repr__(self) -> str:
        return f"<BriefDeliveryLog(id={self.id}, channel={self.delivery_channel}, status={self.status})>"


class BriefTemplate(Base):
    """Templates for brief generation.
    
    Stores reusable templates for generating briefs with consistent
    structure and formatting.
    """
    __tablename__ = "brief_templates"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False
    )
    created_by_user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Template identification
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    template_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Type: daily_brief, weekly_summary, project_update, custom"
    )
    category: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Category: executive, operational, technical, project"
    )
    
    # Template structure
    template_schema: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        comment="Template structure and schema definition"
    )
    sections: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        comment="Template sections and their configuration"
    )
    
    # Generation instructions
    generation_prompt: Mapped[str] = mapped_column(
        Text, 
        nullable=False,
        comment="Prompt template for AI generation"
    )
    data_requirements: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        comment="Required data sources and types"
    )
    output_format: Mapped[str] = mapped_column(
        String(20), 
        default="markdown",
        comment="Output format: markdown, html, json"
    )
    
    # Template configuration
    default_scope: Mapped[str] = mapped_column(
        String(20), 
        default="team",
        comment="Default scope: personal, team, organization"
    )
    default_time_range_hours: Mapped[int] = mapped_column(
        default=24,
        comment="Default time range in hours"
    )
    priority_sources: Mapped[Optional[List[str]]] = mapped_column(
        JSONB,
        comment="Priority data sources for this template"
    )
    
    # Usage and permissions
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    usage_count: Mapped[int] = mapped_column(default=0)
    
    # Quality metrics
    average_rating: Mapped[Optional[float]] = mapped_column(
        comment="Average user rating 1.0-5.0"
    )
    rating_count: Mapped[int] = mapped_column(default=0)
    
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
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="brief_templates")
    created_by: Mapped["User"] = relationship("User", back_populates="created_brief_templates")

    # Constraints
    __table_args__ = (
        Index("idx_brief_templates_org", "organization_id"),
        Index("idx_brief_templates_type", "template_type"),
        Index("idx_brief_templates_category", "category"),
        Index("idx_brief_templates_active", "is_active"),
        Index("idx_brief_templates_public", "is_public"),
        Index("idx_brief_templates_rating", "average_rating"),
        UniqueConstraint("organization_id", "name", name="uq_org_template_name"),
        CheckConstraint(
            "template_type IN ('daily_brief', 'weekly_summary', 'project_update', 'custom', 'team_update')",
            name="check_template_type"
        ),
        CheckConstraint(
            "category IN ('executive', 'operational', 'technical', 'project', 'team')",
            name="check_template_category"
        ),
        CheckConstraint(
            "output_format IN ('markdown', 'html', 'json', 'plain_text')",
            name="check_template_output_format"
        ),
        CheckConstraint(
            "default_scope IN ('personal', 'team', 'organization')",
            name="check_template_default_scope"
        ),
        CheckConstraint(
            "average_rating IS NULL OR (average_rating >= 1.0 AND average_rating <= 5.0)",
            name="check_template_rating_range"
        ),
    )

    def __repr__(self) -> str:
        return f"<BriefTemplate(id={self.id}, name='{self.name}', type={self.template_type})>"