"""Intelligence generation database models for SingleBrief.

This module contains all database models related to brief generation,
query processing, AI responses, and intelligence delivery.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (JSON, Boolean, CheckConstraint, Column, DateTime,
                        Float, ForeignKey, Index, Integer, String, Text,
                        UniqueConstraint)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

class Query(Base):
    """User queries and requests for intelligence.

    Tracks all queries made by users, whether they're ad-hoc questions
    or structured brief requests.
    """

    __tablename__ = "queries"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    conversation_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Query identification
    query_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type: ad_hoc, daily_brief, team_update, project_status, custom_brief",
    )
    priority: Mapped[str] = mapped_column(
        String(20), default="medium", comment="Priority: low, medium, high, urgent"
    )

    # Query content
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    query_intent: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="Detected intent: information_request, status_update, decision_support, etc.",
    )
    query_context: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, comment="Context and parameters for the query"
    )

    # Scope and filtering
    scope: Mapped[str] = mapped_column(
        String(20),
        default="team",
        comment="Scope: personal, team, organization, specific_sources",
    )
    time_range_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    time_range_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    data_sources: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, comment="Specific data sources to include"
    )

    # Processing status
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        comment="Status: pending, processing, completed, failed, cancelled",
    )
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    processing_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    processing_duration_ms: Mapped[Optional[int]] = mapped_column()

    # Result metadata
    response_count: Mapped[int] = mapped_column(default=0)
    sources_used: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSONB, comment="Sources and integrations used to answer the query"
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(
        comment="Overall confidence in the response 0.0-1.0"
    )

    # User feedback
    user_rating: Mapped[Optional[int]] = mapped_column(comment="User rating 1-5 stars")
    user_feedback: Mapped[Optional[str]] = mapped_column(Text)
    feedback_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="queries")
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="queries"
    )
    conversation: Mapped[Optional["Conversation"]] = relationship("Conversation")
    ai_responses: Mapped[List["AIResponse"]] = relationship(
        "AIResponse", back_populates="query", cascade="all, delete-orphan"
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
            name="check_query_type",
        ),
        CheckConstraint(
            "priority IN ('low', 'medium', 'high', 'urgent')",
            name="check_query_priority",
        ),
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')",
            name="check_query_status",
        ),
        CheckConstraint(
            "scope IN ('personal', 'team', 'organization', 'specific_sources')",
            name="check_query_scope",
        ),
        CheckConstraint(
            "confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)",
            name="check_query_confidence_range",
        ),
        CheckConstraint(
            "user_rating IS NULL OR (user_rating >= 1 AND user_rating <= 5)",
            name="check_user_rating_range",
        ),
    )

    def __repr__(self) -> str:
        return f"<Query(id={self.id}, type={self.query_type}, status={self.status})>"

class AIResponse(Base):
    """AI model responses and generation metadata.

    Tracks individual AI responses, including multiple attempts,
    model performance, and response quality metrics.
    """

    __tablename__ = "ai_responses"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    query_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("queries.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Response identification
    response_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type: initial_response, refinement, follow_up, error_recovery",
    )
    attempt_number: Mapped[int] = mapped_column(
        default=1, comment="Attempt number for this response"
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
        String(20), default="text", comment="Format: text, json, markdown, structured"
    )

    # Processing details
    prompt_tokens: Mapped[int] = mapped_column(default=0)
    completion_tokens: Mapped[int] = mapped_column(default=0)
    total_tokens: Mapped[int] = mapped_column(default=0)
    processing_time_ms: Mapped[int] = mapped_column(default=0)

    # Quality metrics
    confidence_score: Mapped[float] = mapped_column(
        default=0.5, comment="Model confidence in response 0.0-1.0"
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
        JSONB, comment="Context and sources used for generation"
    )
    retrieval_results: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSONB, comment="RAG retrieval results and scores"
    )

    # Response status
    status: Mapped[str] = mapped_column(
        String(20),
        default="completed",
        comment="Status: completed, failed, timeout, cancelled",
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    error_type: Mapped[Optional[str]] = mapped_column(String(50))

    # Selection and usage
    is_selected: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Whether this response was selected for the final brief",
    )
    selection_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Cost tracking
    estimated_cost: Mapped[Optional[float]] = mapped_column(
        comment="Estimated cost for this response"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
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
            name="check_response_type",
        ),
        CheckConstraint(
            "response_format IN ('text', 'json', 'markdown', 'structured')",
            name="check_response_format",
        ),
        CheckConstraint(
            "status IN ('completed', 'failed', 'timeout', 'cancelled')",
            name="check_ai_response_status",
        ),
        CheckConstraint(
            "confidence_score >= 0.0 AND confidence_score <= 1.0",
            name="check_ai_confidence_range",
        ),
        CheckConstraint(
            "relevance_score IS NULL OR (relevance_score >= 0.0 AND relevance_score <= 1.0)",
            name="check_relevance_score_range",
        ),
        CheckConstraint(
            "coherence_score IS NULL OR (coherence_score >= 0.0 AND coherence_score <= 1.0)",
            name="check_coherence_score_range",
        ),
        CheckConstraint(
            "completeness_score IS NULL OR (completeness_score >= 0.0 AND completeness_score <= 1.0)",
            name="check_completeness_score_range",
        ),
        CheckConstraint(
            "temperature IS NULL OR (temperature >= 0.0 AND temperature <= 2.0)",
            name="check_temperature_range",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<AIResponse(id={self.id}, model={self.ai_model}, status={self.status})>"
        )

